"""
Web interface for Browser Automation Agent.
Provides a simple UI to give commands to the browser agent.
"""

import os
import threading
import queue
from flask import Flask, render_template_string, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "dev-secret-key")

agent = None
agent_lock = threading.Lock()
task_queue = queue.Queue()
result_queue = queue.Queue()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Automation Agent</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2rem;
        }
        .subtitle {
            text-align: center;
            color: #8892b0;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .input-group {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 14px 18px;
            font-size: 16px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            outline: none;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus {
            border-color: #4f8cff;
        }
        input[type="text"]::placeholder {
            color: #666;
        }
        button {
            padding: 14px 28px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #4f8cff 0%, #3d7be3 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(79, 140, 255, 0.4);
        }
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status.ready {
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid rgba(76, 175, 80, 0.4);
        }
        .status.busy {
            background: rgba(255, 193, 7, 0.2);
            border: 1px solid rgba(255, 193, 7, 0.4);
        }
        .status.error {
            background: rgba(244, 67, 54, 0.2);
            border: 1px solid rgba(244, 67, 54, 0.4);
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .status.ready .status-dot { background: #4caf50; }
        .status.busy .status-dot { background: #ffc107; animation: pulse 1s infinite; }
        .status.error .status-dot { background: #f44336; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .output-area {
            background: #0d1117;
            border-radius: 8px;
            padding: 20px;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .output-area:empty::before {
            content: "Output will appear here...";
            color: #666;
        }
        .examples {
            margin-top: 20px;
        }
        .examples h3 {
            margin-bottom: 12px;
            color: #8892b0;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .example-btn {
            display: inline-block;
            padding: 8px 16px;
            margin: 4px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            color: #8892b0;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .example-btn:hover {
            background: rgba(79, 140, 255, 0.2);
            border-color: rgba(79, 140, 255, 0.4);
            color: #fff;
        }
        .loader {
            display: none;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Browser Automation Agent</h1>
        <p class="subtitle">Control a browser with natural language commands</p>
        
        <div class="card">
            <div id="status" class="status ready">
                <div class="status-dot"></div>
                <span id="status-text">Ready</span>
            </div>
            
            <div class="input-group">
                <input type="text" id="command" placeholder="Enter a command (e.g., 'Go to google.com and search for Python tutorials')" />
                <button id="runBtn" class="btn-primary" onclick="runCommand()">
                    <span id="btnText">Run</span>
                    <div id="loader" class="loader"></div>
                </button>
            </div>
            
            <div class="output-area" id="output"></div>
            
            <div class="examples">
                <h3>Example Commands</h3>
                <span class="example-btn" onclick="setCommand('Go to google.com and search for Python tutorials')">Search Google</span>
                <span class="example-btn" onclick="setCommand('Navigate to github.com and find trending repositories')">GitHub Trending</span>
                <span class="example-btn" onclick="setCommand('Go to news.ycombinator.com and get the top headlines')">Hacker News</span>
                <span class="example-btn" onclick="setCommand('Visit wikipedia.org and search for artificial intelligence')">Wikipedia Search</span>
            </div>
        </div>
    </div>
    
    <script>
        const commandInput = document.getElementById('command');
        const runBtn = document.getElementById('runBtn');
        const btnText = document.getElementById('btnText');
        const loader = document.getElementById('loader');
        const output = document.getElementById('output');
        const status = document.getElementById('status');
        const statusText = document.getElementById('status-text');
        
        function setCommand(cmd) {
            commandInput.value = cmd;
            commandInput.focus();
        }
        
        function setStatus(state, text) {
            status.className = 'status ' + state;
            statusText.textContent = text;
        }
        
        function appendOutput(text) {
            output.textContent += text;
            output.scrollTop = output.scrollHeight;
        }
        
        async function runCommand() {
            const command = commandInput.value.trim();
            if (!command) return;
            
            runBtn.disabled = true;
            btnText.style.display = 'none';
            loader.style.display = 'inline-block';
            output.textContent = '';
            setStatus('busy', 'Executing...');
            
            try {
                const response = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    appendOutput(decoder.decode(value));
                }
                
                setStatus('ready', 'Ready');
            } catch (error) {
                appendOutput('\\nError: ' + error.message);
                setStatus('error', 'Error');
            } finally {
                runBtn.disabled = false;
                btnText.style.display = 'inline';
                loader.style.display = 'none';
            }
        }
        
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCommand();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/run', methods=['POST'])
def run_command():
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    def generate():
        global agent
        
        yield f"Task: {command}\n"
        yield "=" * 50 + "\n\n"
        yield "Starting browser agent...\n"
        
        try:
            from src.browser_agent import create_agent
            
            with agent_lock:
                if agent is None:
                    yield "Initializing browser and AI model...\n"
                    agent = create_agent(headless=True)
                    yield "Browser agent ready!\n\n"
                
                yield "Executing task...\n\n"
                result = agent.run(command)
                yield f"\nResult:\n{result}\n"
                
        except Exception as e:
            yield f"\nError: {str(e)}\n"
            with agent_lock:
                if agent:
                    try:
                        agent.stop()
                    except:
                        pass
                    agent = None
    
    return Response(generate(), mimetype='text/plain')


@app.route('/status')
def get_status():
    global agent
    return jsonify({
        'initialized': agent is not None,
        'ready': True
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
