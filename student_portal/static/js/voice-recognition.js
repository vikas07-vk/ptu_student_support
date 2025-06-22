// static/js/voice-recognition.js
const voiceBtn = document.getElementById('voice-btn');
const userInput = document.getElementById('user-input');

if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-IN';

    voiceBtn.addEventListener('click', () => {
        recognition.start();
        voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        recognition.stop();
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        document.getElementById('send-btn').click();
    };

    recognition.onerror = (event) => {
        console.error(event.error);
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };

    recognition.onend = () => {
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };
} else {
    voiceBtn.style.display = 'none';
}
