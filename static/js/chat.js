document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');

    messageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            sendMessage(message);
            messageInput.value = '';
        }
    });

    const searchInput = document.getElementById('message-search');
    const searchBtn = document.getElementById('search-btn');
    const searchResults = document.getElementById('search-results');

    searchBtn.addEventListener('click', handleSearch);

    searchInput.addEventListener('input', () => {
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        searchTimeout = setTimeout(handleSearch, 300);
    });

    const newGroupForm = document.getElementById('newGroupForm');
    newGroupForm.addEventListener('submit', handleNewGroupFormSubmit);
});

function appendMessage(username, message, timestamp) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'mb-2';
    messageDiv.innerHTML = `
        <small class="text-muted">${timestamp}</small>
        <strong>${username}:</strong> ${message}
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendStatusMessage(message) {
    const messagesContainer = document.getElementById('messages');
    const statusDiv = document.createElement('div');
    statusDiv.className = 'text-center text-muted mb-2';
    statusDiv.textContent = message;
    messagesContainer.appendChild(statusDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        searchResults.classList.add('d-none');
        return;
    }

    try {
        const response = await fetch(`/search_messages?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (response.ok) {
            displaySearchResults(data.results);
        } else {
            throw new Error(data.error || 'Search failed');
        }
    } catch (error) {
        console.error('Search error:', error);
        showError('Failed to search messages', searchInput.parentElement);
    }
}

function displaySearchResults(results) {
    searchResults.innerHTML = '';
    searchResults.classList.remove('d-none');
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">No messages found</div>';
        return;
    }
    
    results.forEach(result => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'search-result-item';
        resultDiv.innerHTML = `
            <div class="result-header">
                <span class="result-username">${result.username}</span>
                <span class="result-time">${result.timestamp}</span>
            </div>
            <div class="result-content">${result.content}</div>
        `;
        resultDiv.addEventListener('click', () => {
            window.location.href = `/chat/${result.chat_id}`;
        });
        searchResults.appendChild(resultDiv);
    });
}

async function handleNewGroupFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch(e.target.action, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create group');
        }
        
        const data = await response.json();
        window.location.href = `/chat/group/${data.group_id}`;
        
    } catch (error) {
        console.error('Error creating group:', error);
        showError(error.message || 'Failed to create group', newGroupForm);
    }
}
