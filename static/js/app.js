let currentEpicId = null;
let currentEditingACId = null;

function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    errorAlert.textContent = message;
    errorAlert.classList.remove('d-none');
    setTimeout(() => {
        errorAlert.classList.add('d-none');
    }, 5000);
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (show) {
        spinner.classList.remove('d-none');
    } else {
        spinner.classList.add('d-none');
    }
}

async function fetchEpic() {
    const epicId = document.getElementById('epicId').value.trim();
    if (!epicId) {
        showError('Please enter an EPIC ID');
        return;
    }

    showLoading(true);
    try {
        const response = await fetch(`/api/epic/${epicId}`);
        const data = await response.json();

        if (!response.ok) {
            if (data.needs_settings) {
                showError(data.error);
                setTimeout(() => {
                    showSettings();
                }, 2000);
            } else {
                showError(data.error || 'Failed to fetch EPIC');
            }
            showLoading(false);
            return;
        }

        currentEpicId = data.epic.id;
        displayEpicDetails(data.epic, data.stories);
        showLoading(false);

    } catch (error) {
        showError('Unable to connect to server. Please try again.');
        showLoading(false);
    }
}

function displayEpicDetails(epic, stories) {
    document.getElementById('epicDetails').classList.remove('d-none');
    document.getElementById('epicTitle').textContent = epic.title;
    document.getElementById('epicDescription').textContent = epic.description || 'No description available';

    const storiesList = document.getElementById('storiesList');
    const storyCount = document.getElementById('storyCount');
    storyCount.textContent = stories.length;

    if (stories.length === 0) {
        storiesList.innerHTML = '<p class="text-muted">No existing user stories found for this EPIC.</p>';
    } else {
        storiesList.innerHTML = stories.map(story => `
            <div class="card story-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0"><i class="fas fa-bookmark"></i> ${story.jira_id}: ${story.title}</h6>
                        <button class="btn btn-sm btn-outline-primary" onclick="checkStoryAlignment(${story.id})">
                            <i class="fas fa-check-circle"></i> Check Alignment
                        </button>
                    </div>
                    <p class="text-muted small mb-2">${story.description || 'No description'}</p>
                    <div class="ac-text small">
                        <strong>Current AC:</strong><br>
                        ${story.current_ac || '<em>No acceptance criteria defined</em>'}
                    </div>
                </div>
            </div>
        `).join('');
    }
}

async function checkStoryAlignment(storyId) {
    showLoading(true);
    try {
        const response = await fetch(`/api/story/${storyId}/check-alignment`, {
            method: 'POST'
        });
        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Failed to check story alignment');
            showLoading(false);
            return;
        }

        displayAlignmentResult(data.alignment, data.story);
        showLoading(false);

    } catch (error) {
        showError('Unable to check alignment. Please try again.');
        showLoading(false);
    }
}

function displayAlignmentResult(alignment, story) {
    const alignmentColor = alignment.aligned ? 'success' : 'warning';
    const alignmentIcon = alignment.aligned ? 'check-circle' : 'exclamation-triangle';
    
    const modalContent = `
        <div class="modal fade" id="alignmentModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-${alignmentIcon} text-${alignmentColor}"></i>
                            Story Alignment Check: ${story.title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-${alignmentColor}">
                            <strong>Alignment Score:</strong> ${alignment.alignment_score}%<br>
                            <strong>Status:</strong> ${alignment.aligned ? 'Aligned with EPIC' : 'Needs Update'}
                        </div>
                        <h6>Analysis:</h6>
                        <p>${alignment.reasoning}</p>
                        ${alignment.changes_needed && alignment.changes_needed.length > 0 ? `
                            <h6>Recommended Changes:</h6>
                            <ul>
                                ${alignment.changes_needed.map(change => `<li>${change}</li>`).join('')}
                            </ul>
                        ` : ''}
                        <h6>Current AC:</h6>
                        <div class="ac-text mb-3">${story.current_ac || 'None'}</div>
                        ${!alignment.aligned ? `
                            <h6>Suggested AC:</h6>
                            <textarea id="suggestedACText" class="form-control ac-text" rows="10" readonly>${alignment.suggested_ac}</textarea>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        ${!alignment.aligned ? `
                            <button type="button" class="btn btn-primary" data-story-id="${story.id}" id="acceptACBtn">
                                Accept Suggested AC
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('alignmentModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalContent);
    const modal = new bootstrap.Modal(document.getElementById('alignmentModal'));
    
    const acceptBtn = document.getElementById('acceptACBtn');
    if (acceptBtn) {
        acceptBtn.addEventListener('click', function() {
            const storyId = this.getAttribute('data-story-id');
            const suggestedAC = document.getElementById('suggestedACText').value;
            acceptSuggestedAC(storyId, suggestedAC);
            modal.hide();
        });
    }
    
    modal.show();
}

async function acceptSuggestedAC(storyId, suggestedAC) {
    showLoading(true);
    try {
        const response = await fetch(`/api/story/${storyId}/update-ac`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ac_text: suggestedAC
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            showError(data.error || 'Failed to update acceptance criteria');
            showLoading(false);
            return;
        }
        
        showLoading(false);
        location.reload();
        
    } catch (error) {
        showError('Unable to update AC. Please try again.');
        showLoading(false);
    }
}

async function generateAC() {
    if (!currentEpicId) return;

    showLoading(true);
    try {
        const response = await fetch(`/api/epic/${currentEpicId}/generate-ac`, {
            method: 'POST'
        });
        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Failed to generate acceptance criteria');
            showLoading(false);
            return;
        }

        displayGeneratedAC(data.generated_acs);
        showLoading(false);

    } catch (error) {
        showError('Unable to generate AC. Please try again.');
        showLoading(false);
    }
}

async function analyzeCoverage() {
    if (!currentEpicId) return;

    showLoading(true);
    try {
        const response = await fetch(`/api/epic/${currentEpicId}/analyze-coverage`, {
            method: 'POST'
        });
        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Failed to analyze coverage');
            showLoading(false);
            return;
        }

        displayCoverageAnalysis(data.coverage_analysis, data.generated_acs);
        showLoading(false);

    } catch (error) {
        showError('Unable to analyze coverage. Please try again.');
        showLoading(false);
    }
}

function displayCoverageAnalysis(coverage, acs) {
    const section = document.getElementById('generatedACSection');
    const list = document.getElementById('generatedACList');
    section.classList.remove('d-none');

    const coveragePercent = coverage.coverage_percentage || 0;
    const coverageColor = coveragePercent >= 80 ? 'success' : coveragePercent >= 50 ? 'warning' : 'danger';
    
    const updatedCount = coverage.updated_stories?.length || 0;
    const newCount = coverage.new_story_suggestions?.length || 0;
    const redundantCount = coverage.redundant_stories?.length || 0;
    
    let html = `
        <div class="alert alert-${coverageColor} mb-4">
            <h6><i class="fas fa-chart-pie"></i> Coverage Analysis Summary</h6>
            <p class="mb-2">${coverage.summary || 'Analysis complete'}</p>
            <div class="progress mb-3" style="height: 25px;">
                <div class="progress-bar bg-${coverageColor}" role="progressbar" 
                     style="width: ${coveragePercent}%">${coveragePercent}% Coverage</div>
            </div>
            <div class="row text-center">
                <div class="col-md-4">
                    <strong class="text-warning">${updatedCount}</strong>
                    <br><small>Stories Need Update</small>
                </div>
                <div class="col-md-4">
                    <strong class="text-success">${newCount}</strong>
                    <br><small>New Story Suggestions</small>
                </div>
                <div class="col-md-4">
                    <strong class="text-danger">${redundantCount}</strong>
                    <br><small>Potentially Redundant</small>
                </div>
            </div>
        </div>
    `;
    
    if (redundantCount > 0) {
        html += `
            <div class="alert alert-warning mb-4">
                <h6><i class="fas fa-exclamation-triangle"></i> Potentially Redundant Stories</h6>
                <p>The following stories may be redundant or duplicate. Consider reviewing them:</p>
                <ul class="mb-0">
                    ${coverage.redundant_stories.map(rs => `
                        <li><strong>${rs.jira_id || rs.story_title || 'Unknown Story'}:</strong> ${rs.reason}</li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    if (acs.length > 0) {
        html += `<h6 class="mb-3"><i class="fas fa-tasks"></i> Recommended Actions (${acs.length} total)</h6>`;
        html += acs.map(ac => {
            const status = ac.is_new ? 'New Story' : 'Update Existing';
            const badge = ac.is_new ? 'success' : 'warning';
            return `
                <div class="card ac-card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="ac_${ac.id}" data-ac-id="${ac.id}" checked>
                                <label class="form-check-label" for="ac_${ac.id}">
                                    <strong>${ac.story_title}</strong>
                                </label>
                            </div>
                            <span class="badge bg-${badge}">${status}</span>
                        </div>
                        <div class="ac-text" id="ac_text_${ac.id}">${ac.ac_text}</div>
                        <div class="mt-3">
                            <button class="btn btn-sm btn-primary" onclick="editAC(${ac.id})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        html += `<div class="alert alert-success"><i class="fas fa-check-circle"></i> All EPIC items are already covered in existing user stories. No updates needed.</div>`;
    }
    
    list.innerHTML = html;
}

function displayGeneratedAC(acs) {
    const section = document.getElementById('generatedACSection');
    const list = document.getElementById('generatedACList');
    section.classList.remove('d-none');

    const totalACs = acs.reduce((sum, ac) => sum + (ac.ac_text.split('\n').filter(line => line.trim().startsWith('Given') || line.trim().startsWith('When') || line.trim().startsWith('Then')).length), 0);
    
    let html = `
        <div class="alert alert-info mb-4">
            <h6><i class="fas fa-lightbulb"></i> AI-Suggested Stories</h6>
            <p class="mb-2">The following user stories and acceptance criteria have been generated from the EPIC description.</p>
            <div class="row text-center">
                <div class="col-md-6">
                    <strong class="text-primary">${acs.length}</strong>
                    <br><small>Total Suggested Stories</small>
                </div>
                <div class="col-md-6">
                    <strong class="text-success">${totalACs}</strong>
                    <br><small>Total Acceptance Criteria</small>
                </div>
            </div>
            <div class="mt-3">
                <small class="text-muted">
                    <strong>Status:</strong> Pending Creation | 
                    <strong>Action Required:</strong> Review, modify, approve, or discard each suggestion before creating in Jira
                </small>
            </div>
        </div>
    `;

    html += `<h6 class="mb-3"><i class="fas fa-tasks"></i> Story Suggestions (${acs.length} total)</h6>`;
    html += acs.map(ac => `
        <div class="card ac-card mb-3" id="card_${ac.id}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="ac_${ac.id}" data-ac-id="${ac.id}" checked>
                        <label class="form-check-label" for="ac_${ac.id}">
                            <strong>${ac.story_title}</strong>
                        </label>
                    </div>
                    <span class="badge bg-info">AI-Suggested</span>
                </div>
                <div class="ac-text" id="ac_text_${ac.id}">${ac.ac_text}</div>
                <div class="mt-3 d-flex gap-2">
                    <button class="btn btn-sm btn-primary" onclick="editAC(${ac.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-success" onclick="updateSingleStory(${ac.id})">
                        <i class="fas fa-upload"></i> Update to Jira
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    list.innerHTML = html;
}

function editAC(acId) {
    currentEditingACId = acId;
    const acText = document.getElementById(`ac_text_${acId}`).textContent;
    const storyTitle = document.querySelector(`label[for="ac_${acId}"] strong`).textContent;

    document.getElementById('editStoryTitle').value = storyTitle;
    document.getElementById('editACText').value = acText;
    document.getElementById('chatACPreview').textContent = acText;
    document.getElementById('chatMessages').innerHTML = `
        <div class="text-muted">
            <p><strong>AI Assistant:</strong> How would you like to refine the acceptance criteria? Examples:</p>
            <ul>
                <li>"Make it more technical"</li>
                <li>"Add edge cases for invalid input"</li>
                <li>"Simplify the language"</li>
                <li>"Convert to Gherkin format"</li>
            </ul>
        </div>
    `;

    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

async function saveManualEdit() {
    const storyTitle = document.getElementById('editStoryTitle').value;
    const acText = document.getElementById('editACText').value;

    try {
        const response = await fetch(`/api/ac/${currentEditingACId}/edit-manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ story_title: storyTitle, ac_text: acText })
        });

        const data = await response.json();
        if (response.ok) {
            document.getElementById(`ac_text_${currentEditingACId}`).textContent = data.ac.ac_text;
            document.querySelector(`label[for="ac_${currentEditingACId}"] strong`).textContent = data.ac.story_title;

            const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
            modal.hide();
            showError = () => {};
            alert('Changes saved successfully!');
        } else {
            showError(data.error || 'Failed to save changes');
        }
    } catch (error) {
        showError('Unable to save changes. Please try again.');
    }
}

async function sendChatMessage() {
    const message = document.getElementById('chatInput').value.trim();
    if (!message) return;

    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML += `
        <div class="chat-message chat-user">
            <strong>You:</strong> ${message}
        </div>
    `;

    document.getElementById('chatInput').value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    chatMessages.innerHTML += `
        <div class="chat-message chat-ai">
            <strong>AI:</strong> <span class="spinner-border spinner-border-sm"></span> Processing...
        </div>
    `;

    try {
        const response = await fetch(`/api/ac/${currentEditingACId}/edit-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (response.ok) {
            chatMessages.querySelector('.chat-ai:last-child').innerHTML = `
                <strong>AI:</strong> I've refined the acceptance criteria based on your request.
            `;

            document.getElementById('chatACPreview').textContent = data.ac.ac_text;
            document.getElementById('editACText').value = data.ac.ac_text;
            document.getElementById(`ac_text_${currentEditingACId}`).textContent = data.ac.ac_text;
        } else {
            chatMessages.querySelector('.chat-ai:last-child').innerHTML = `
                <strong>AI:</strong> <span class="text-danger">Error: ${data.error}</span>
            `;
        }
    } catch (error) {
        chatMessages.querySelector('.chat-ai:last-child').innerHTML = `
            <strong>AI:</strong> <span class="text-danger">Error: Unable to process request</span>
        `;
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function updateSingleStory(acId) {
    if (!confirm('Update this story in Jira with the current acceptance criteria?')) {
        return;
    }

    try {
        const response = await fetch('/api/stories/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                updates: [{
                    story_id: acId,
                    ac_id: acId
                }]
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('Story updated successfully in Jira!');
        } else {
            showError(data.error || 'Failed to update story');
        }
    } catch (error) {
        showError('Unable to update story. Please try again.');
    }
}

async function updateSelectedStories() {
    const checkboxes = document.querySelectorAll('.form-check-input:checked');
    if (checkboxes.length === 0) {
        showError('Please select at least one story to update');
        return;
    }

    if (!confirm(`Update ${checkboxes.length} selected ${checkboxes.length === 1 ? 'story' : 'stories'} in Jira?`)) {
        return;
    }

    const updates = Array.from(checkboxes).map(cb => ({
        story_id: parseInt(cb.dataset.acId),
        ac_id: parseInt(cb.dataset.acId)
    }));

    try {
        const response = await fetch('/api/stories/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ updates })
        });

        const data = await response.json();
        if (response.ok) {
            const successCount = data.results.filter(r => r.success).length;
            alert(`Successfully updated ${successCount} of ${updates.length} stories in Jira!`);
        } else {
            showError(data.error || 'Failed to update stories');
        }
    } catch (error) {
        showError('Unable to update stories. Please try again.');
    }
}

function showSettings() {
    loadSettings();
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    modal.show();
}

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();

        document.getElementById('jiraUrl').value = data.jira_url || '';
        document.getElementById('jiraUsername').value = data.jira_username || '';
    } catch (error) {
        console.error('Failed to load settings', error);
    }
}

async function saveSettings() {
    const settings = {
        jira_url: document.getElementById('jiraUrl').value,
        jira_username: document.getElementById('jiraUsername').value,
        jira_password: document.getElementById('jiraPassword').value
    };

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
            modal.hide();
            alert('Settings saved successfully!');
        } else {
            showError('Failed to save settings');
        }
    } catch (error) {
        showError('Unable to save settings. Please try again.');
    }
}

document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        if (e.target.id === 'epicId') {
            fetchEpic();
        } else if (e.target.id === 'chatInput') {
            sendChatMessage();
        }
    }
});
