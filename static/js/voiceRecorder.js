// static/js/voiceRecorder.js

/**
 * Voice recording with optional Speech-to-Text transcription.
 *
 * STT providers:
 *   "disabled"       — record audio as file attachment (original behavior)
 *   "browser"        — use Web Speech API for real-time transcription
 *   "local"          — send recording to server /api/stt/transcribe (Whisper)
 *   "endpoint:<id>"  — send recording to server /api/stt/transcribe (API)
 */

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recordingStartTime = null;
let recordingInterval = null;

// Browser STT state
let _recognition = null;
let _browserTranscript = '';

// Cached STT provider — refreshed on settings change
let _sttProvider = 'browser';

/**
 * Fetch current STT provider from server settings
 */
async function refreshSttProvider() {
  try {
    const res = await fetch('/api/stt/stats', { credentials: 'same-origin' });
    if (res.ok) {
      const stats = await res.json();
      _sttProvider = stats.provider || 'browser';
      if (_sttProvider === 'disabled') _sttProvider = 'browser';
      // Notify the send button to update its icon
      if (window._updateSendBtnIcon) window._updateSendBtnIcon();
    }
  } catch (e) {
    _sttProvider = 'browser';
  }
}

/**
 * Format seconds as MM:SS
 */
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
  const secs = (seconds % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
}

/**
 * Reset UI state after recording ends
 */
function _resetRecordingUI() {
  isRecording = false;
  if (recordingInterval) {
    clearInterval(recordingInterval);
    recordingInterval = null;
  }
  // Reset voice button
  const voiceBtn = document.getElementById('voice-input-btn');
  if (voiceBtn) {
    voiceBtn.classList.remove('recording');
    voiceBtn.title = 'Speak to convert voice to text';
  }
  // Reset send button via global callback
  const sendBtn = document.querySelector('.send-btn');
  if (sendBtn) {
    sendBtn.classList.remove('recording');
    sendBtn.dataset.mode = '';
  }
  if (window._updateSendBtnIcon) {
    setTimeout(window._updateSendBtnIcon, 50);
  }
}

/**
 * Start browser speech recognition alongside recording
 */
function startBrowserSTT(onInterim) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  _browserTranscript = '';
  _recognition = new SpeechRecognition();
  _recognition.continuous = true;
  _recognition.interimResults = true;
  _recognition.lang = navigator.language || 'en-US';

  _recognition.onresult = (event) => {
    let interim = '';
    let finalStr = '';
    for (let i = 0; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        finalStr += event.results[i][0].transcript + ' ';
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    _browserTranscript = finalStr;
    const input = document.getElementById('message');
    if (input && (finalStr || interim)) {
      const current = (finalStr + (interim ? ' ' + interim : '')).trim();
      if (current) {
        input.value = current;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  };

  _recognition.onerror = (e) => {
    console.warn('Browser STT error:', e.error);
  };

  try {
    _recognition.start();
  } catch (e) {
    console.debug('Recognition already started:', e);
  }
}

function stopBrowserSTT() {
  if (_recognition) {
    try { _recognition.stop(); } catch (e) { /* ignore */ }
    _recognition = null;
  }
  return _browserTranscript.trim();
}

/**
 * Send audio to server for transcription
 */
async function transcribeOnServer(audioBlob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.webm');

  const res = await fetch('/api/stt/transcribe', {
    method: 'POST',
    credentials: 'same-origin',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || 'Transcription failed');
  }

  const data = await res.json();
  return data.text || '';
}

/**
 * Insert transcribed text into the chat input
 */
function insertTranscription(text, showToast) {
  if (!text) return;
  const input = document.getElementById('message');
  if (!input) return;

  const existing = input.value.trim();
  if (!existing.includes(text.trim())) {
    input.value = existing ? existing + ' ' + text : text;
  }

  // Trigger auto-resize and icon update
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.focus();

  if (showToast) showToast('Voice converted to text! 🎙️✨');
}

/**
 * Start voice recording
 */
export function startRecording(onFileCreated, showToast, showError) {
  const voiceBtn = document.getElementById('voice-input-btn');
  if (voiceBtn) {
    voiceBtn.classList.add('recording');
    voiceBtn.title = 'Listening... Click to stop and transcribe';
  }

  // Check for SpeechRecognition first
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    isRecording = true;
    startBrowserSTT();
    if (showToast) showToast('Listening... Speak now 🎙️');
  }

  // Also record audio stream if mediaDevices available
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    audioChunks = [];
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        try {
          mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        } catch (e) {
          mediaRecorder = new MediaRecorder(stream);
        }

        mediaRecorder.ondataavailable = event => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          const transcript = stopBrowserSTT();

          if (transcript) {
            insertTranscription(transcript, showToast);
          } else if (audioChunks.length > 0) {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            try {
              if (showToast) showToast('Transcribing audio...', 4000);
              const serverTranscript = await transcribeOnServer(audioBlob);
              if (serverTranscript) {
                insertTranscription(serverTranscript, showToast);
              } else {
                if (showToast) showToast('No speech detected');
              }
            } catch (e) {
              if (onFileCreated) {
                const audioFile = new File([audioBlob], `voice-${Date.now()}.webm`, { type: 'audio/webm' });
                onFileCreated(audioFile);
              }
            }
          }

          _resetRecordingUI();
        };

        mediaRecorder.start();
        isRecording = true;
      })
      .catch(error => {
        console.warn('Microphone stream warning:', error);
        if (!SpeechRecognition) {
          if (showError) showError('Microphone access denied or not supported.');
          _resetRecordingUI();
        }
      });
  } else if (!SpeechRecognition) {
    if (showError) showError('Speech recognition not supported in this browser.');
    _resetRecordingUI();
  }
}

/**
 * Stop voice recording
 */
export function stopRecording() {
  const transcript = stopBrowserSTT();
  if (transcript) {
    insertTranscription(transcript);
  }
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  } else {
    _resetRecordingUI();
  }
}

/**
 * Check if currently recording
 */
export function getIsRecording() {
  return isRecording;
}

/**
 * Initialize recording state & wire up #voice-input-btn
 */
export function init() {
  isRecording = false;
  refreshSttProvider();

  // Attach click listener to #voice-input-btn
  const voiceBtn = document.getElementById('voice-input-btn');
  if (voiceBtn && !voiceBtn.__voiceBound) {
    voiceBtn.__voiceBound = true;
    voiceBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (isRecording) {
        stopRecording();
      } else {
        startRecording(
          (audioFile) => {
            if (window.fileHandlerModule) window.fileHandlerModule.addFiles([audioFile]);
          },
          (msg, timeout) => {
            if (window.uiModule && window.uiModule.showToast) window.uiModule.showToast(msg, timeout);
          },
          (err) => {
            if (window.uiModule && window.uiModule.showError) window.uiModule.showError(err);
          }
        );
      }
    });
  }
}

const voiceRecorderModule = {
  startRecording,
  stopRecording,
  getIsRecording,
  init,
  refreshSttProvider,
  get _sttProvider() { return _sttProvider; },
  set _sttProvider(v) { _sttProvider = v; },
};

export default voiceRecorderModule;

