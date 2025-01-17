let currentUtterance = null;
let isPaused = false;

function readWithTTS(text) {
    stopTTS();
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.onend = () => {
        document.getElementById('playPauseIcon').className = 'fas fa-play';
        document.getElementById('progressBar').style.width = '0%';
    };
    currentUtterance.onboundary = event => {
        const progress = (event.charIndex / text.length) * 100;
        document.getElementById('progressBar').style.width = `${progress}%`;
    };
    speechSynthesis.speak(currentUtterance);
    document.getElementById('audioControls').classList.remove('hidden');
    document.getElementById('playPauseIcon').className = 'fas fa-pause';
}

function toggleTTS() {
    if (speechSynthesis.speaking) {
        if (isPaused) {
            speechSynthesis.resume();
            document.getElementById('playPauseIcon').className = 'fas fa-pause';
        } else {
            speechSynthesis.pause();
            document.getElementById('playPauseIcon').className = 'fas fa-play';
        }
        isPaused = !isPaused;
    }
}

function stopTTS() {
    speechSynthesis.cancel();
    currentUtterance = null;
    isPaused = false;
    document.getElementById('audioControls').classList.add('hidden');
    document.getElementById('progressBar').style.width = '0%';
}

function closeTTSControls() {
    stopTTS();
    document.getElementById('audioControls').classList.add('hidden');
}
