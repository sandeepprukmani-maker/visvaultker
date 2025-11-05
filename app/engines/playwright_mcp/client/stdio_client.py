"""
STDIO-based MCP Client for Playwright MCP Server
Launches MCP server as subprocess and communicates via JSON-RPC over stdio
"""
import json
import os
import subprocess
import threading
import queue
import configparser
from typing import Dict, List, Any, Optional
import time


class MCPStdioClient:
    """Client for Model Context Protocol communication via STDIO transport"""
    
    def __init__(self, headless: bool = True, browser: str = 'chromium'):
        """
        Initialize MCP client with subprocess
        
        Args:
            headless: Run browser in headless mode (defaults to True)
            browser: Browser to use (defaults to 'chromium')
        """
        # Only read browser type from config, not headless mode
        # User's UI selection for headless should take precedence
        config = configparser.ConfigParser()
        try:
            config.read('config/config.ini')
            if config.has_section('browser'):
                # Only override browser type, not headless setting
                browser = config.get('browser', 'browser', fallback=browser)
        except Exception:
            # Use the provided defaults if config file is missing or invalid
            pass
        
        self.request_id = 0
        self.initialized = False
        self.available_tools = []
        self.process = None
        self.response_queue = queue.Queue()
        self.pending_requests = {}
        self.reader_thread = None
        self.stderr_thread = None
        
        args = ["node", "integrations/playwright_mcp_node/cli.js"]
        if headless:
            args.append("--headless")
        args.append(f"--browser={browser}")
        
        env = os.environ.copy()
        env['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'
        
        self.process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=env
        )
        
        self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
        self.reader_thread.start()
        
        self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.stderr_thread.start()
        
        time.sleep(0.2)
    
    def _read_responses(self):
        """Background thread to read responses from subprocess"""
        try:
            while self.process and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        response = json.loads(line)
                        if "id" in response:
                            req_id = response["id"]
                            if req_id in self.pending_requests:
                                self.pending_requests[req_id].put(response)
                        else:
                            self.response_queue.put(response)
                    except json.JSONDecodeError:
                        pass
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"Reader thread error: {e}")
    
    def _read_stderr(self):
        """Background thread to drain stderr and prevent deadlock"""
        try:
            while self.process and self.process.poll() is None:
                try:
                    line = self.process.stderr.readline()
                    if not line:
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"Stderr thread error: {e}")
    
    def _next_id(self) -> int:
        """Generate next request ID"""
        self.request_id += 1
        return self.request_id
    
    def _make_request(self, method: str, params: Optional[Dict] = None, timeout: int = 30) -> Dict:
        """
        Make a JSON-RPC request via STDIO
        
        Args:
            method: JSON-RPC method name
            params: Optional parameters for the method
            timeout: Request timeout in seconds
            
        Returns:
            Response from the server
        """
        if not self.process or self.process.poll() is not None:
            raise Exception("MCP server process is not running")
        
        request_id = self._next_id()
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }
        
        if params is not None:
            payload["params"] = params
        
        response_queue = queue.Queue()
        self.pending_requests[request_id] = response_queue
        
        try:
            request_line = json.dumps(payload) + "\n"
            self.process.stdin.write(request_line)
            self.process.stdin.flush()
            
            try:
                response = response_queue.get(timeout=timeout)
                
                if "error" in response:
                    raise Exception(f"MCP Error: {response['error']}")
                
                return response.get("result", {})
                
            except queue.Empty:
                raise Exception(f"Request timeout after {timeout}s")
                
        finally:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
    
    def initialize(self) -> Dict:
        """Initialize the MCP connection"""
        if self.initialized:
            return {"status": "already_initialized"}
        
        result = self._make_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": False}
            },
            "clientInfo": {
                "name": "playwright-web-agent",
                "version": "1.0.0"
            }
        })
        
        self.initialized = True
        return result
    
    def list_tools(self) -> List[Dict]:
        """
        List available tools from the MCP server
        
        Returns:
            List of available tools with their schemas
        """
        if not self.initialized:
            self.initialize()
        
        result = self._make_request("tools/list", {})
        self.available_tools = result.get("tools", [])
        return self.available_tools
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        if not self.initialized:
            self.initialize()
        
        result = self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        }, timeout=90)
        
        return result
    
    def get_tools_schema(self) -> List[Dict]:
        """
        Get tools in OpenAI function calling format
        
        Returns:
            List of tools formatted for OpenAI
        """
        if not self.available_tools:
            self.list_tools()
        
        openai_tools = []
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    def close(self):
        """Close the MCP client and subprocess"""
        if self.process:
            try:
                self.call_tool("browser_close", {})
            except:
                pass
            
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
