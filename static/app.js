const API_BASE = '';

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

function showLoading() {
    document.getElementById('loading').classList.add('visible');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('visible');
}

function showResult(elementId, content, isError = false) {
    const resultBox = document.getElementById(elementId);
    resultBox.innerHTML = content;
    resultBox.classList.add('visible');
}

document.getElementById('crawl-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('crawl-url').value;
    const depth = parseInt(document.getElementById('crawl-depth').value);
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/crawl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, depth, save_version: true })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResult('crawl-result', `
                <h3 class="success">✓ Crawl Successful</h3>
                <div class="metric-card">
                    <h4>Summary</h4>
                    <p><strong>Pages Crawled:</strong> ${data.pages_crawled}</p>
                    <p><strong>Templates Found:</strong> ${data.unique_templates}</p>
                </div>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `);
        } else {
            showResult('crawl-result', `
                <h3 class="error">✗ Crawl Failed</h3>
                <p>${data.detail || 'An error occurred'}</p>
            `, true);
        }
    } catch (error) {
        showResult('crawl-result', `
            <h3 class="error">✗ Network Error</h3>
            <p>${error.message}</p>
        `, true);
    } finally {
        hideLoading();
    }
});

document.getElementById('automate-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const startUrl = document.getElementById('auto-url').value;
    const task = document.getElementById('auto-task').value;
    const enableVision = document.getElementById('enable-vision').checked;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task,
                start_url: startUrl,
                context_limit: 10,
                enable_vision: enableVision,
                vision_threshold: 0.75
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const status = data.execution?.status || data.status;
            const isSuccess = status === 'success';
            
            showResult('automate-result', `
                <h3 class="${isSuccess ? 'success' : 'error'}">${isSuccess ? '✓' : '✗'} Automation ${isSuccess ? 'Completed' : 'Failed'}</h3>
                <div class="metric-card">
                    <h4>Task</h4>
                    <p>${task}</p>
                </div>
                ${data.execution ? `
                <div class="metric-card">
                    <h4>Execution Results</h4>
                    <p><strong>Status:</strong> ${data.execution.status}</p>
                    <p><strong>Steps Completed:</strong> ${data.execution.steps_completed || 0}</p>
                    <p><strong>Steps Failed:</strong> ${data.execution.steps_failed || 0}</p>
                </div>
                ` : ''}
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `);
        } else {
            showResult('automate-result', `
                <h3 class="error">✗ Automation Failed</h3>
                <p>${data.detail || 'An error occurred'}</p>
            `, true);
        }
    } catch (error) {
        showResult('automate-result', `
            <h3 class="error">✗ Network Error</h3>
            <p>${error.message}</p>
        `, true);
    } finally {
        hideLoading();
    }
});

document.getElementById('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const query = document.getElementById('search-query').value;
    const topK = parseInt(document.getElementById('search-top-k').value);
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, top_k: topK })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            let resultsHtml = `<h3 class="success">✓ Found ${data.results_count} Results</h3>`;
            
            if (data.results && data.results.length > 0) {
                data.results.forEach((result, index) => {
                    resultsHtml += `
                        <div class="metric-card">
                            <h4>Result ${index + 1} (Similarity: ${(result.similarity * 100).toFixed(1)}%)</h4>
                            <p><strong>Selector:</strong> <code>${result.selector}</code></p>
                            <p><strong>Description:</strong> ${result.description}</p>
                        </div>
                    `;
                });
            }
            
            resultsHtml += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            showResult('search-result', resultsHtml);
        } else {
            showResult('search-result', `
                <h3 class="error">✗ Search Failed</h3>
                <p>${data.detail || 'An error occurred'}</p>
            `, true);
        }
    } catch (error) {
        showResult('search-result', `
            <h3 class="error">✗ Network Error</h3>
            <p>${error.message}</p>
        `, true);
    } finally {
        hideLoading();
    }
});

async function loadMetrics() {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/metrics/dashboard`);
        const data = await response.json();
        
        if (response.ok) {
            let metricsHtml = '<h3 class="success">✓ System Metrics</h3>';
            
            if (data.summary) {
                metricsHtml += `
                    <div class="metric-card">
                        <h4>Summary</h4>
                        <p><strong>Total Crawls:</strong> ${data.summary.total_crawls || 0}</p>
                        <p><strong>Total Automations:</strong> ${data.summary.total_automations || 0}</p>
                        <p><strong>Unique URLs:</strong> ${data.summary.unique_urls_crawled || 0}</p>
                    </div>
                `;
            }
            
            if (data.success_rates) {
                metricsHtml += `
                    <div class="metric-card">
                        <h4>Success Rates</h4>
                        <p><strong>Crawls:</strong> ${(data.success_rates.crawls * 100).toFixed(1)}%</p>
                        <p><strong>Automations:</strong> ${(data.success_rates.automations * 100).toFixed(1)}%</p>
                    </div>
                `;
            }
            
            metricsHtml += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            showResult('metrics-result', metricsHtml);
        } else {
            showResult('metrics-result', `
                <h3 class="error">✗ Failed to Load Metrics</h3>
                <p>${data.detail || 'An error occurred'}</p>
            `, true);
        }
    } catch (error) {
        showResult('metrics-result', `
            <h3 class="error">✗ Network Error</h3>
            <p>${error.message}</p>
        `, true);
    } finally {
        hideLoading();
    }
}
