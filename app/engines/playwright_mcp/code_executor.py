"""
Python Code Executor
Safely executes generated Playwright scripts and captures results/errors
"""
import asyncio
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CodeExecutor:
    """
    Executes Python Playwright scripts and captures output/errors
    """
    
    def __init__(self, timeout: int = 120):
        """
        Initialize Code Executor
        
        Args:
            timeout: Maximum execution time in seconds (default: 120)
        """
        self.timeout = timeout
        self.logger = logger
    
    async def execute_script(
        self,
        python_code: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Execute a Python Playwright script
        
        Args:
            python_code: The Python code to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results:
            {
                'success': bool,
                'output': str,
                'error': str | None,
                'exit_code': int,
                'execution_time': float
            }
        """
        try:
            if progress_callback:
                progress_callback('executor_init', {
                    'message': '▶️ Code Executor: Preparing to run script...'
                })
            
            self.logger.info("▶️ Code Executor: Starting script execution")
            
            # Create temporary file for the script
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(python_code)
                script_path = temp_file.name
            
            try:
                if progress_callback:
                    progress_callback('executor_running', {
                        'message': '▶️ Code Executor: Running Playwright script...',
                        'timeout': self.timeout
                    })
                
                start_time = datetime.now()
                
                # Execute the script
                process = await asyncio.create_subprocess_exec(
                    'python',
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=os.environ.copy()
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout
                    )
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    stdout_text = stdout.decode('utf-8') if stdout else ''
                    stderr_text = stderr.decode('utf-8') if stderr else ''
                    exit_code = process.returncode
                    
                    success = exit_code == 0
                    
                    if success:
                        if progress_callback:
                            progress_callback('executor_success', {
                                'message': '✅ Code Executor: Script executed successfully!',
                                'execution_time': execution_time
                            })
                        
                        self.logger.info(f"✅ Code Executor: Success (took {execution_time:.2f}s)")
                        
                        return {
                            'success': True,
                            'output': stdout_text,
                            'error': None,
                            'exit_code': exit_code,
                            'execution_time': execution_time,
                            'stderr': stderr_text if stderr_text else None
                        }
                    else:
                        if progress_callback:
                            progress_callback('executor_failed', {
                                'message': '❌ Code Executor: Script execution failed',
                                'exit_code': exit_code
                            })
                        
                        self.logger.error(f"❌ Code Executor: Failed with exit code {exit_code}")
                        
                        return {
                            'success': False,
                            'output': stdout_text,
                            'error': stderr_text or 'Script execution failed',
                            'exit_code': exit_code,
                            'execution_time': execution_time
                        }
                
                except asyncio.TimeoutError:
                    if progress_callback:
                        progress_callback('executor_timeout', {
                            'message': f'⏱️ Code Executor: Timeout after {self.timeout}s',
                        })
                    
                    self.logger.error(f"⏱️ Code Executor: Timeout after {self.timeout}s")
                    
                    # Kill the process
                    try:
                        process.kill()
                        await process.wait()
                    except:
                        pass
                    
                    return {
                        'success': False,
                        'output': '',
                        'error': f'Script execution timed out after {self.timeout} seconds',
                        'exit_code': -1,
                        'execution_time': self.timeout
                    }
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(script_path)
                except:
                    pass
        
        except Exception as e:
            self.logger.error(f"❌ Code Executor: Unexpected error: {e}", exc_info=True)
            
            if progress_callback:
                progress_callback('executor_error', {
                    'message': f'❌ Code Executor: Error - {str(e)}'
                })
            
            return {
                'success': False,
                'output': '',
                'error': f'Executor error: {str(e)}',
                'exit_code': -1,
                'execution_time': 0.0
            }
    
    def extract_error_summary(self, error_text: str) -> str:
        """
        Extract a concise error summary from stderr
        
        Args:
            error_text: Full error text from stderr
            
        Returns:
            Concise error summary
        """
        if not error_text:
            return "Unknown error"
        
        lines = error_text.strip().split('\n')
        
        # Look for the actual error message (usually the last few lines)
        error_lines = []
        for line in reversed(lines):
            if line.strip():
                error_lines.insert(0, line)
                if len(error_lines) >= 5:  # Get last 5 meaningful lines
                    break
        
        return '\n'.join(error_lines)
