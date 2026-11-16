// محرك المؤثرات الصوتية والمؤقت الزمني عبر Web Audio API
let audioCtx = null, masterGain = null;

function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext();
    masterGain = audioCtx.createGain();
    masterGain.gain.value = 0.5;
    masterGain.connect(audioCtx.destination);
  }
  if (audioCtx.state === 'suspended') audioCtx.resume();
}

function setVolume(val) {
  if (!masterGain) initAudio();
  masterGain.gain.value = Math.max(0, Math.min(1, val));
}

function playTone(freq, type, duration, delay = 0) {
  initAudio();
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, audioCtx.currentTime + delay);
  gain.gain.setValueAtTime(0.3, audioCtx.currentTime + delay);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + delay + duration);
  osc.connect(gain);
  gain.connect(masterGain);
  osc.start(audioCtx.currentTime + delay);
  osc.stop(audioCtx.currentTime + delay + duration);
}

function playTick() { playTone(800, 'sine', 0.08); }
function playWarning() { playTone(1200, 'square', 0.15); }
function playTimeout() {
  playTone(250, 'sawtooth', 0.8);
  setTimeout(() => playTone(180, 'sawtooth', 1.0), 200);
}
function playCorrect() {
  playTone(523.25, 'triangle', 0.2);
  playTone(659.25, 'triangle', 0.2, 0.15);
  playTone(783.99, 'triangle', 0.4, 0.3);
}
function playWrong() {
  playTone(350, 'sawtooth', 0.25);
  playTone(280, 'sawtooth', 0.35, 0.15);
}

let timerInterval = null, remainingSeconds = 45, isPaused = false;
let onTickCallback = null, onTimeoutCallback = null;

function startTimer(duration, onTick, onTimeout) {
  clearInterval(timerInterval);
  remainingSeconds = duration;
  isPaused = false;
  onTickCallback = onTick;
  onTimeoutCallback = onTimeout;
  if (onTickCallback) onTickCallback(remainingSeconds);

  timerInterval = setInterval(() => {
    if (isPaused) return;
    remainingSeconds--;
    playTick();
    if (remainingSeconds === 15) playWarning();
    if (onTickCallback) onTickCallback(remainingSeconds);

    if (remainingSeconds <= 0) {
      clearInterval(timerInterval);
      playTimeout();
      if (onTimeoutCallback) onTimeoutCallback();
    }
  }, 1000);
}

function pauseTimer() { isPaused = true; }
function resumeTimer() { isPaused = false; }
function stopTimer() { clearInterval(timerInterval); }
