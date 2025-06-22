document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatContainer = document.getElementById('chat-container');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const typingIndicator = document.getElementById('typing-indicator');
    const quickLinksToggle = document.getElementById('quick-links-toggle');
    const quickLinksSidebar = document.getElementById('quick-links-sidebar');
    const closeSidebar = document.getElementById('close-sidebar');
    const liveSupportBtn = document.getElementById('live-support');
    const liveSupportModal = document.getElementById('live-support-modal');
    const closeModal = document.getElementById('close-modal');
    const supportForm = document.getElementById('support-form');
    const quickQueryLinks = document.querySelectorAll('.quick-query');
    const suggestionLinks = document.querySelectorAll('.suggestion');

    // Toggle quick links sidebar
    quickLinksToggle.addEventListener('click', function() {
        quickLinksSidebar.classList.add('active');
    });

    closeSidebar.addEventListener('click', function() {
        quickLinksSidebar.classList.remove('active');
    });

    // Toggle live support modal
    liveSupportBtn.addEventListener('click', function() {
        liveSupportModal.classList.add('active');
    });

    closeModal.addEventListener('click', function() {
        liveSupportModal.classList.remove('active');
    });

    liveSupportModal.addEventListener('click', function(e) {
        if (e.target === liveSupportModal) {
            liveSupportModal.classList.remove('active');
        }
    });

    // Handle quick query links
    quickQueryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const query = this.getAttribute('data-query');
            userInput.value = query;
            quickLinksSidebar.classList.remove('active');
            userInput.focus();
        });
    });

    // Handle suggestion links
    suggestionLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const query = this.getAttribute('data-query');
            sendMessage(query);
        });
    });

    // Handle Live Support form submission
    supportForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const query = document.getElementById('query').value;

        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        fetch('/live_support', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}&query=${encodeURIComponent(query)}`

        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addBotMessage('Your support request has been submitted successfully. We will contact you soon.');
                supportForm.reset();
                liveSupportModal.classList.remove('active');
            } else {
                addBotMessage('Failed to send email. Error: ' + data.error);
            }
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Request';
        })
        .catch(error => {
            console.error('Error:', error);
            addBotMessage('There was a problem sending your support request.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Request';
        });
    });                                                                                       

// Chat send button
    sendBtn.addEventListener('click', function() {
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });

    // Chat enter key
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const message = userInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });

    // Send message function
    function sendMessage(message) {
        addUserMessage(message);
        userInput.value = '';
        typingIndicator.classList.add('active');
        scrollToBottom();

        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
           body: `user_query=${encodeURIComponent(message)}`

        })
        .then(response => response.json())
        .then(data => {
            typingIndicator.classList.remove('active');
            addBotMessage(data.response);
            scrollToBottom();
        })
        .catch(error => {
            typingIndicator.classList.remove('active');
            addBotMessage("I'm having trouble connecting to the server. Please try again later.");
            console.error('Error:', error);
            scrollToBottom();
        });
    }

    // Add user message
    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = text;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = getCurrentTime();

        messageContent.appendChild(messageText);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatMessages.appendChild(messageDiv);
    }

    // Add bot message
    function addBotMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = text.replace(/\n/g, '<br>');

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = getCurrentTime();

        messageContent.appendChild(messageText);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatMessages.appendChild(messageDiv);
    }

    // Time helper
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    scrollToBottom();
});        