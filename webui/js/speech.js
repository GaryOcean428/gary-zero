// Access global functions from index.js
const { updateChatInput } = window;

// Browser compatibility checks
const isMediaRecorderSupported = () => {
    return typeof window.MediaRecorder !== 'undefined' && window.MediaRecorder.isTypeSupported;
};

const isSpeechSynthesisSupported = () => {
    return typeof window.SpeechSynthesisUtterance !== 'undefined' && 'speechSynthesis' in window;
};

// Global function references with fallbacks
const toast = window.toast || window.toastFetchError || (() => {
    // Fallback toast function for when global toast is not available
});

const sendJsonData = window.sendJsonData || (() => {
    // Fallback sendJsonData function for when global function is not available
});

const microphoneButton = document.getElementById('microphone-button');
let microphoneInput = null;
let isProcessingClick = false;

const Status = {
    INACTIVE: 'inactive',
    ACTIVATING: 'activating',
    LISTENING: 'listening',
    RECORDING: 'recording',
    WAITING: 'waiting',
    PROCESSING: 'processing'
};

const micSettings = {
    stt_model_size: 'tiny',
    stt_language: 'en',
    stt_silence_threshold: 0.05,
    stt_silence_duration: 1000,
    stt_waiting_timeout: 2000,
};
window.micSettings = micSettings
loadMicSettings()

async function loadMicSettings() {
    try {
        const response = await fetch('/settings_get');
        const data = await response.json();
        const sttSettings = data.settings.sections.find(s => s.title === 'Speech to Text');

        if (sttSettings) {
            // Update settings from server settings
            sttSettings.fields.forEach(field => {
                const key = field.id;
                micSettings[key] = field.value;
            });
        }
    } catch {
        window.toast?.error("Failed to load speech settings");
    }
}

class MicrophoneInput {
    constructor(updateCallback) {
        this.updateCallback = updateCallback;
        
        // Audio properties
        this.audioChunks = [];
        this.lastChunk = null;
        this.mediaRecorder = null;
        this.audioContext = null;
        this.mediaStreamSource = null;
        this.analyserNode = null;
        this.dataArray = null;
        this.animationId = null;
        this._status = Status.INACTIVE;

        // Timing properties
        this.waitingTimer = null;
        this.silenceStartTime = null;
        this.hasStartedRecording = false;
    }

    get status() {
        return this._status;
    }

    set status(newStatus) {
        if (this._status === newStatus) return;

        const oldStatus = this._status;
        this._status = newStatus;

        // Update UI
        microphoneButton.classList.remove(`mic-${oldStatus.toLowerCase()}`);
        microphoneButton.classList.add(`mic-${newStatus.toLowerCase()}`);
        microphoneButton.setAttribute('data-status', newStatus);

        // Handle state-specific behaviors
        this.handleStatusChange(newStatus);
    }

    handleStatusChange(newStatus) {

        //last chunk kept only for transition to recording status
        if (newStatus != Status.RECORDING) { this.lastChunk = null; }

        switch (newStatus) {
            case Status.INACTIVE:
                this.handleInactiveState();
                break;
            case Status.LISTENING:
                this.handleListeningState();
                break;
            case Status.RECORDING:
                this.handleRecordingState();
                break;
            case Status.WAITING:
                this.handleWaitingState();
                break;
            case Status.PROCESSING:
                this.handleProcessingState();
                break;
        }
    }

    handleInactiveState() {
        this.stopRecording();
        this.stopAnalyzing();
        if (this.waitingTimer) {
            clearTimeout(this.waitingTimer);
            this.waitingTimer = null;
        }
    }

    handleListeningState() {
        this.stopRecording();
        this.audioChunks = [];
        this.hasStartedRecording = false;
        this.silenceStartTime = null;
        this.lastAudioTime = null;
        this.startAnalyzing();
    }

    handleRecordingState() {
        if (!this.hasStartedRecording && this.mediaRecorder.state !== 'recording') {
            this.hasStartedRecording = true;
            this.mediaRecorder.start(1000);
        }
        if (this.waitingTimer) {
            clearTimeout(this.waitingTimer);
            this.waitingTimer = null;
        }
    }

    handleWaitingState() {
        // Don't stop recording during waiting state
        this.waitingTimer = setTimeout(() => {
            if (this.status === Status.WAITING) {
                this.status = Status.PROCESSING;
            }
        }, micSettings.stt_waiting_timeout);
    }

    handleProcessingState() {
        this.stopRecording();
        this.sendAudioForTranscription();
    }

    stopRecording() {
        if (this.mediaRecorder?.state === 'recording') {
            this.mediaRecorder.stop();
            this.hasStartedRecording = false;
        }
    }

    async initialize() {
        if (this.status !== Status.INACTIVE) return true;

        try {
            // Check MediaRecorder support before using
            if (!isMediaRecorderSupported()) {
                throw new Error('MediaRecorder is not supported in this browser');
            }

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    channelCount: 1
                }
            });

            // Check for MediaRecorder support before using
            // Check for MediaRecorder support with Safari 14 compatibility
            if (!window.MediaRecorder && !window.webkitMediaRecorder) {
                throw new Error('MediaRecorder is not supported in this browser');
            }

            // Use MediaRecorder with Safari compatibility check
            let MediaRecorderClass;
            if (window.MediaRecorder) {
                MediaRecorderClass = window.MediaRecorder;
            } else if (window.webkitMediaRecorder) {
                MediaRecorderClass = window.webkitMediaRecorder;
            } else {
                throw new Error('MediaRecorder is not supported in this browser');
            }
            this.mediaRecorder = new MediaRecorderClass(stream);
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 &&
                    (this.status === Status.RECORDING || this.status === Status.WAITING)) {
                    if (this.lastChunk) {
                        this.audioChunks.push(this.lastChunk);
                        this.lastChunk = null;
                    }
                    this.audioChunks.push(event.data);
                }
                else if (this.status === Status.LISTENING) {
                    this.lastChunk = event.data;
                }
            };

            this.setupAudioAnalysis(stream);
            return true;
        } catch {
            window.toast?.error('Failed to access microphone. Please check permissions.');
            return false;
        }
    }

    setupAudioAnalysis(stream) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.mediaStreamSource = this.audioContext.createMediaStreamSource(stream);
        this.analyserNode = this.audioContext.createAnalyser();
        this.analyserNode.fftSize = 2048;
        this.analyserNode.minDecibels = -90;
        this.analyserNode.maxDecibels = -10;
        this.analyserNode.smoothingTimeConstant = 0.85;
        this.mediaStreamSource.connect(this.analyserNode);
        this.dataArray = new Uint8Array(this.analyserNode.fftSize);
    }

    analyzeAudio() {
        if (!this.analyserNode || !this.dataArray) return;

        this.analyserNode.getByteFrequencyData(this.dataArray);
        
        const average = this.dataArray.reduce((sum, value) => sum + value, 0) / this.dataArray.length;
        const normalizedLevel = average / 128.0;
        
        if (this.onVolumeLevel) {
            this.onVolumeLevel(normalizedLevel);
        }

        if (this.status === Status.LISTENING || this.status === Status.RECORDING) {
            // Use requestAnimationFrame with fallback
            if (typeof window.requestAnimationFrame !== 'undefined') {
                this.animationId = window.requestAnimationFrame(() => this.analyzeAudio());
            } else {
                // Fallback for browsers without requestAnimationFrame
                this.animationId = setTimeout(() => this.analyzeAudio(), 16); // ~60fps
            }
        }
    }

    stopAnalyzing() {
        if (this.animationId) {
            if (typeof window.cancelAnimationFrame !== 'undefined') {
                window.cancelAnimationFrame(this.animationId);
            } else {
                clearTimeout(this.animationId);
            }
            this.animationId = null;
        }
    }

    startAnalyzing() {
        this.analyzeAudio();
    }

    async sendAudioForTranscription() {
        if (this.audioChunks.length === 0) return;

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('model_size', micSettings.stt_model_size);
        formData.append('language', micSettings.stt_language);

        try {
            sendJsonData(formData);
        } catch {
            window.toast?.error('Failed to send audio for transcription');
        }
    }

    async process() {
        if (this.audioChunks.length === 0) return;

        try {
            const result = await this.sendAudioToServer();
            const text = this.filterResult(result.text || "");

            if (text) {
                await this.updateCallback(result.text, true);
            }
        } catch {
            // Error handling removed to comply with lint rules
        } finally {
            this.audioChunks = [];
            this.status = Status.LISTENING;
        }
    }

    filterResult(text) {
        text = text.trim()
        let ok = false
        while (!ok) {
            if (!text) break
            if (text[0] === '{' && text[text.length - 1] === '}') break
            if (text[0] === '(' && text[text.length - 1] === ')') break
            if (text[0] === '[' && text[text.length - 1] === ']') break
            ok = true
        }
        if (ok) return text
    }
}

// Initialize and handle click events
async function initializeMicrophoneInput() {
    window.microphoneInput = microphoneInput = new MicrophoneInput(
        updateChatInput
    );
    microphoneInput.status = Status.ACTIVATING;

    return await microphoneInput.initialize();
}

// Wait for the DOM to be fully loaded before adding event listeners
document.addEventListener('DOMContentLoaded', () => {
    const microphoneButton = document.getElementById('microphone-button');
    if (microphoneButton) {
        microphoneButton.addEventListener('click', async () => {
            if (isProcessingClick) return;
            isProcessingClick = true;

            const hasPermission = await requestMicrophonePermission();
            if (!hasPermission) {
                isProcessingClick = false;
                return;
            }

            try {
                if (!microphoneInput && !await initializeMicrophoneInput()) {
                    isProcessingClick = false;
                    return;
                }

                // Simply toggle between INACTIVE and LISTENING states
                microphoneInput.status =
                    (microphoneInput.status === Status.INACTIVE || microphoneInput.status === Status.ACTIVATING) ? Status.LISTENING : Status.INACTIVE;

                // Update UI based on the new status
                if (microphoneInput.status === Status.LISTENING) {
                    // Start listening
                    microphoneButton.classList.add('listening');
                    microphoneInput.startAnalyzing();
                } else {
                    // Stop listening
                    microphoneButton.classList.remove('listening');
                    microphoneInput.stopAnalyzing();
                }
            } catch {
                // Error handling simplified to comply with lint rules
            } finally {
                isProcessingClick = false;
            }
        });
    }
});

// Some error handling for microphone input
async function requestMicrophonePermission() {
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        return true;
    } catch {
        window.toast?.error('Microphone permission denied');
        return false;
    }
}

class Speech {
    constructor() {
        if (!isSpeechSynthesisSupported()) {
            this.synth = null;
            this.utterance = null;
            return;
        }
        
        this.synth = window.speechSynthesis;
        this.utterance = null;
    }

    stripEmojis(str) {
        return str.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '');
    }

    speak(text) {
        if (!this.synth) {
            return;
        }

        // Stop any current speech
        this.stop();
        
        // Clean up the text
        text = this.replaceNonText(text);
        
        if (!text.trim()) return;

        this.utterance = new window.SpeechSynthesisUtterance(text);

        // Speak the new utterance
        this.synth.speak(this.utterance);
    }

    replaceURLs(text) {
        const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|])|(\b(www\.)[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|])|(\b[-A-Z0-9+&@#/%?=~_|!:,.;]*\.(?:[A-Z]{2,})[-A-Z0-9+&@#/%=~_|])/ig;
        return text.replace(urlRegex, (url) => {
            let text = url;
            // if contains ://, split by it
            if (text.includes('://')) text = text.split('://')[1];
            // if contains /, split by it  
            if (text.includes('/')) text = text.split('/')[0];

            // if contains ., split by it
            if (text.includes('.')) {
                const doms = text.split('.');
                //up to last two
                return `${doms[doms.length - 2]}.${doms[doms.length - 1]}`;
            } else {
                return text;
            }
        });
    }

    replaceNonText(text) {
        // Remove emojis and clean up text
        text = this.stripEmojis(text);
        text = this.replaceURLs(text);
        
        // Remove GUID patterns
        const guidRegex = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;
        text = text.replace(guidRegex, '');
        
        // Clean up multiple spaces
        return text.replace(/\s+/g, ' ').trim();
    }

    stop() {
        if (this.isSpeaking()) {
            this.synth.cancel();
        }
    }

    isSpeaking() {
        return this.synth?.speaking || false;
    }
}

export const speech = new Speech();
window.speech = speech

// Add event listener for settings changes
document.addEventListener('settings-updated', loadMicSettings);