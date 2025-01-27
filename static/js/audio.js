// static/js/audio.js
class TTSManager {
    constructor() {
        this.currentUtterance = null;
        this.isPaused = false;
        this.text = '';
        this.progressInterval = null;
    }

    init() {
        if (!('speechSynthesis' in window)) {
            console.error('Text-to-speech not supported');
            return false;
        }
        return true;
    }

    createAudioControls() {
        const controls = document.createElement('div');
        controls.id = 'audioControls';
        controls.className = 'fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg p-4 flex items-center space-x-4 z-50';
        controls.innerHTML = `
            <button onclick="ttsManager.togglePlayPause()" class="w-10 h-10 rounded-full bg-violet-600 text-white flex items-center justify-center hover:bg-violet-700">
                <i id="playPauseIcon" class="fas fa-pause"></i>
            </button>
            <div class="w-64 bg-gray-200 rounded-full h-2 overflow-hidden">
                <div id="progressBar" class="bg-violet-600 h-full w-0 transition-all"></div>
            </div>
            <button onclick="ttsManager.stop()" class="text-gray-600 hover:text-gray-800">
                <i class="fas fa-times"></i>
            </button>
        `;
        document.body.appendChild(controls);
    }

    read(text) {
        if (!this.init()) return;
        
        this.stop();
        this.text = text;
        
        this.currentUtterance = new SpeechSynthesisUtterance(text);
        this.currentUtterance.rate = 1;
        this.currentUtterance.pitch = 1;
        this.currentUtterance.volume = 1;
        
        this.currentUtterance.onend = () => this.stop();
        this.currentUtterance.onerror = (event) => {
            console.error('TTS Error:', event);
            this.stop();
        };

        this.createAudioControls();
        speechSynthesis.speak(this.currentUtterance);
        this.startProgress();
    }

    togglePlayPause() {
        if (!this.currentUtterance) return;
        
        if (this.isPaused) {
            speechSynthesis.resume();
            document.getElementById('playPauseIcon').className = 'fas fa-pause';
            this.startProgress();
        } else {
            speechSynthesis.pause();
            document.getElementById('playPauseIcon').className = 'fas fa-play';
            this.stopProgress();
        }
        this.isPaused = !this.isPaused;
    }

    stop() {
        speechSynthesis.cancel();
        this.currentUtterance = null;
        this.isPaused = false;
        this.stopProgress();
        
        const controls = document.getElementById('audioControls');
        if (controls) {
            controls.remove();
        }
    }

    startProgress() {
        this.stopProgress();
        const startTime = Date.now();
        const duration = (this.text.length / 5) * 1000; // Approximate duration based on text length
        
        this.progressInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min((elapsed / duration) * 100, 100);
            const progressBar = document.getElementById('progressBar');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            if (progress >= 100) {
                this.stopProgress();
            }
        }, 100);
    }

    stopProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
}

// Initialize TTS Manager
const ttsManager = new TTSManager();

// Update the readWithTTS function to use the new manager
function readWithTTS(text) {
    ttsManager.read(text);
}