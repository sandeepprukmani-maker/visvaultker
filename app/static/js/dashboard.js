let currentMode = 'headful';  // Default to headful (show browser window)
let currentEngine = 'browser_use';
let isExecuting = false;

// Function to toggle script panels visibility based on engine
function toggleScriptPanels(engineType) {
    const scriptPanelsContainer = document.getElementById('script-panels-container');
    if (scriptPanelsContainer) {
        if (engineType === 'browser_use') {
            scriptPanelsContainer.style.display = 'none';
        } else {
            scriptPanelsContainer.style.display = 'grid';
        }
    }
}

// Function to show/hide healed script panel
function toggleHealedScriptPanel(show) {
    const healedPanel = document.getElementById('healed-script-panel');
    if (healedPanel) {
        healedPanel.style.display = show ? 'block' : 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const headlessBtn = document.getElementById('headless-btn');
    const headfulBtn = document.getElementById('headful-btn');
    const browserUseBtn = document.getElementById('browser-use-btn');
    const playwrightMcpBtn = document.getElementById('playwright-mcp-btn');
    const executeBtn = document.getElementById('execute-automation');
    const promptTextarea = document.getElementById('automation-prompt');
    
    // Initialize visibility on page load
    toggleScriptPanels(currentEngine);
    
    if (headlessBtn) {
        headlessBtn.addEventListener('click', () => {
            currentMode = 'headless';
            headlessBtn.classList.add('active');
            headfulBtn.classList.remove('active');
        });
    }
    
    if (headfulBtn) {
        headfulBtn.addEventListener('click', () => {
            currentMode = 'headful';
            headfulBtn.classList.add('active');
            headlessBtn.classList.remove('active');
        });
    }
    
    if (browserUseBtn) {
        browserUseBtn.addEventListener('click', () => {
            currentEngine = 'browser_use';
            browserUseBtn.classList.add('active');
            playwrightMcpBtn.classList.remove('active');
            toggleScriptPanels('browser_use');
        });
    }
    
    if (playwrightMcpBtn) {
        playwrightMcpBtn.addEventListener('click', () => {
            currentEngine = 'playwright_mcp';
            playwrightMcpBtn.classList.add('active');
            browserUseBtn.classList.remove('active');
            toggleScriptPanels('playwright_mcp');
        });
    }
    
    if (executeBtn) {
        executeBtn.addEventListener('click', async () => {
            if (isExecuting) return;
            
            const instruction = promptTextarea.value.trim();
            if (!instruction) {
                alert('Please enter an automation instruction');
                return;
            }
            
            isExecuting = true;
            executeBtn.disabled = true;
            executeBtn.innerHTML = '<span class="spinner"></span> Executing...';
            
            document.getElementById('generated-script').innerHTML = '<div style="color: var(--text-secondary);">Waiting for automation to start...</div>';
            document.getElementById('execution-logs').innerHTML = '<div style="color: var(--text-secondary);">Connecting to automation server...</div>';
            
            // Hide healed script panel at start (only show if healing occurs)
            toggleHealedScriptPanel(false);
            
            // Hide copy button at start of execution
            const copyBtn = document.getElementById('copy-playwright-code');
            if (copyBtn) {
                copyBtn.style.display = 'none';
                copyBtn.onclick = null;
            }
            
            let stepLogs = [];
            
            try {
                const apiKey = localStorage.getItem('api_key');
                
                // Use Server-Sent Events for real-time streaming
                const payload = {
                    instruction: instruction,
                    engine: currentEngine,
                    headless: currentMode === 'headless'
                };
                
                // Create SSE connection
                const url = '/api/execute/stream';
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(apiKey ? {'X-API-Key': apiKey} : {})
                    },
                    body: JSON.stringify(payload)
                });
                
                // Handle non-OK HTTP responses before entering streaming loop
                if (!response.ok) {
                    let errorData;
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        errorData = {error: 'Unknown error', message: 'Failed to get error details'};
                    }
                    
                    // Reset script panel and hide copy button on error
                    document.getElementById('generated-script').innerHTML = 
                        `<div class="empty-state"><div>No script generated</div></div>`;
                    const copyBtn = document.getElementById('copy-playwright-code');
                    if (copyBtn) {
                        copyBtn.style.display = 'none';
                        copyBtn.onclick = null;
                    }
                    
                    let errorMessage = '';
                    if (response.status === 401 || response.status === 403) {
                        errorMessage = '🔒 Authentication Error<br>Please provide a valid API key.';
                    } else if (response.status === 429) {
                        errorMessage = '⏱️ Rate Limit Exceeded<br>' + (errorData.message || 'Too many requests. Please try again later.');
                    } else {
                        errorMessage = `❌ ${errorData.error || 'Error'}<br>${errorData.message || 'An unexpected error occurred'}`;
                    }
                    
                    document.getElementById('execution-logs').innerHTML = 
                        `<div style="color: var(--error-text);">${errorMessage}</div>`;
                    return;
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, {stream: true});
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (!line.trim() || !line.startsWith('data: ')) continue;
                        
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            // Handle different event types from SSE stream
                            if (data.type === 'start') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">${data.message || 'Starting automation...'}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'init') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">⚙️  ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'browser_init') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">🌐 ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'agent_create') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">🤖 ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'execution_start') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">▶️  ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'step') {
                                stepLogs.push(`<div style="color: var(--success-text); margin: 3px 0;">✓ Step ${data.data.step_number}/${data.data.total_steps}: ${data.data.action}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                                // Auto-scroll to bottom
                                const logsElement = document.getElementById('execution-logs');
                                logsElement.scrollTop = logsElement.scrollHeight;
                            } else if (data.type === 'screenshot') {
                                // Display screenshot in real-time
                                const screenshotPanel = document.getElementById('screenshot-panel');
                                const screenshotPath = data.data.path;
                                const screenshotUrl = data.data.url || '';
                                
                                // Convert local file path to URL (assuming static serving)
                                const publicPath = screenshotPath.replace(/\\/g, '/');
                                
                                screenshotPanel.innerHTML = `
                                    <div style="text-align: center;">
                                        <img src="/${publicPath}" alt="Automation Screenshot" 
                                             style="max-width: 100%; height: auto; border-radius: 4px; cursor: pointer;" 
                                             onclick="window.open('/${publicPath}', '_blank')"
                                             onerror="this.parentElement.innerHTML='<div class=\\'empty-state\\'><div>Screenshot capture failed</div></div>'">
                                        ${screenshotUrl ? `<div style="margin-top: 8px; color: var(--text-secondary); font-size: 0.85rem;">📍 ${screenshotUrl}</div>` : ''}
                                    </div>`;
                                stepLogs.push(`<div style="color: var(--success-text); margin: 3px 0;">📸 Screenshot captured</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'done') {
                                const result = data.result;
                                
                                // Display generated code in the Generated Script panel
                                const scriptPanel = document.getElementById('generated-script');
                                const copyBtn = document.getElementById('copy-playwright-code');
                                
                                if (result.playwright_code) {
                                    // Show the code with syntax highlighting
                                    scriptPanel.innerHTML = 
                                        `<pre style="color: var(--success-text); margin: 0; white-space: pre-wrap; font-size: 0.85rem; font-family: 'Monaco', 'Courier New', monospace; line-height: 1.5;"><code class="language-python">${escapeHtml(result.playwright_code)}</code></pre>`;
                                    
                                    // Show copy button
                                    copyBtn.style.display = 'block';
                                    copyBtn.onclick = () => copyToClipboard(result.playwright_code);
                                } else {
                                    // No code generated - reset to empty state
                                    scriptPanel.innerHTML = 
                                        `<div class="empty-state">
                                            <div>No script generated for this automation</div>
                                        </div>`;
                                    
                                    // Hide copy button and clear handler
                                    copyBtn.style.display = 'none';
                                    copyBtn.onclick = null;
                                }
                                
                                // Display healed code in the Healed Script panel if available
                                const healedScriptPanel = document.getElementById('healed-script');
                                if (result.healed_code) {
                                    // Show healed script panel since healing occurred
                                    toggleHealedScriptPanel(true);
                                    healedScriptPanel.innerHTML = 
                                        `<pre style="color: var(--warning-text); margin: 0; white-space: pre-wrap; font-size: 0.85rem; font-family: 'Monaco', 'Courier New', monospace; line-height: 1.5;"><code class="language-python">${escapeHtml(result.healed_code)}</code></pre>`;
                                } else {
                                    // No healed code - keep panel hidden
                                    toggleHealedScriptPanel(false);
                                }
                                
                                // Add final summary
                                stepLogs.push(`<div style="color: var(--success-text); margin-top: 10px; font-weight: bold;">✅ Completed successfully in ${result.iterations || 0} steps</div>`);
                                if (result.final_result) {
                                    stepLogs.push(`<div style="color: var(--success-text); margin-top: 5px;">Result: ${result.final_result}</div>`);
                                }
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                                break;
                            } else if (data.type === 'error') {
                                // Reset script panel and hide copy button on error
                                document.getElementById('generated-script').innerHTML = 
                                    `<div class="empty-state"><div>No script generated due to error</div></div>`;
                                const copyBtn = document.getElementById('copy-playwright-code');
                                if (copyBtn) {
                                    copyBtn.style.display = 'none';
                                    copyBtn.onclick = null;
                                }
                                
                                stepLogs.push(`<div style="color: var(--error-text); font-weight: bold; margin-top: 10px;">❌ ${data.error || 'Execution failed'}</div>`);
                                if (data.message) {
                                    stepLogs.push(`<pre style="color: var(--error-text); margin: 5px 0; white-space: pre-wrap; font-size: 0.85rem;">${data.message}</pre>`);
                                }
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                                break;
                            }
                        } catch (parseError) {
                            console.error('Failed to parse SSE data:', parseError);
                        }
                    }
                }
            } catch (error) {
                console.error('Execution error:', error);
                // Reset script panel and hide copy button on network error
                document.getElementById('generated-script').innerHTML = 
                    `<div class="empty-state"><div>No script generated due to network error</div></div>`;
                const copyBtn = document.getElementById('copy-playwright-code');
                if (copyBtn) {
                    copyBtn.style.display = 'none';
                    copyBtn.onclick = null;
                }
                document.getElementById('execution-logs').innerHTML = 
                    `<div style="color: var(--error-text);">❌ Network Error<br>Failed to execute automation: ${error.message}</div>`;
            } finally {
                isExecuting = false;
                executeBtn.disabled = false;
                executeBtn.innerHTML = '<span>▶️</span> Execute Automation';
            }
        });
    }
});

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper function to copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        const copyBtn = document.getElementById('copy-playwright-code');
        const originalContent = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i data-feather="check"></i>';
        feather.replace();
        setTimeout(() => {
            copyBtn.innerHTML = originalContent;
            feather.replace();
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        alert('Failed to copy code to clipboard');
    }
}
