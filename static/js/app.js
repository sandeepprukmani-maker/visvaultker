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
                    <h6><i class="fas fa-bookmark"></i> ${story.jira_id}: ${story.title}</h6>
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

function displayGeneratedAC(acs) {
    const section = document.getElementById('generatedACSection');
    const list = document.getElementById('generatedACList');
    section.classList.remove('d-none');

    list.innerHTML = acs.map(ac => `
        <div class="card ac-card mb-3">
            <div class="card-body">
                <div class="form-check mb-2">
                    <input class="form-check-input" type="checkbox" id="ac_${ac.id}" data-ac-id="${ac.id}">
                    <label class="form-check-label" for="ac_${ac.id}">
                        <strong>${ac.story_title}</strong>
                    </label>
                </div>
                <div class="ac-text" id="ac_text_${ac.id}">${ac.ac_text}</div>
                <div class="mt-3">
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
