// محرك المؤثرات الصوتية والمؤقت الزمني عبر Web Audio والأصوات الواقعية
let audioCtx = null, masterGain = null;
let correctAudio = new Audio('/audio/applause.mp3');
let wrongAudio = new Audio('/audio/wrong.mp3');

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
  const v = Math.max(0, Math.min(1, val));
  masterGain.gain.value = v;
  const aCorr = document.getElementById('audio-correct') || correctAudio;
  const aWr = document.getElementById('audio-wrong') || wrongAudio;
  if (aCorr) aCorr.volume = v;
  if (aWr) aWr.volume = v;
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

// تدرج حدة التايمر كل 15 ثانية (هادئ 520Hz، ثم متوسط 780Hz، ثم حاد 1100Hz)
function playTick(sec) {
  let freq = 520;
  if (sec <= 15) {
    freq = 1100;
  } else if (sec <= 30) {
    freq = 780;
  }
  playTone(freq, 'sine', 0.08);
}

function playWarning() {
  playTone(1100, 'square', 0.12);
  setTimeout(() => playTone(1200, 'square', 0.15), 140);
}

function playTimeout() {
  playTone(250, 'sawtooth', 0.8);
  setTimeout(() => playTone(180, 'sawtooth', 1.0), 200);
}

function playChime() {
  playTone(523.25, 'sine', 0.18, 0);
  playTone(659.25, 'sine', 0.22, 0.12);
  playTone(783.99, 'sine', 0.35, 0.24);
}

// تشغيل تصفيق حار واقعي وحقيقي للمسابقات
function playCorrect() {
  initAudio();
  try {
    const el = document.getElementById('audio-correct') || correctAudio;
    if (el) {
      el.pause();
      el.currentTime = 0;
      el.volume = masterGain ? masterGain.gain.value : 0.6;
      const p = el.play();
      if (p !== undefined) p.catch(e => console.log('Correct audio error:', e));
    }
  } catch (e) {
    console.log('Error playing correct audio:', e);
  }
}

// تشغيل موسيقى الخسارة الحقيقية لمسابقات التلفزيون (Sad Trombone)
function playWrong() {
  initAudio();
  try {
    const el = document.getElementById('audio-wrong') || wrongAudio;
    if (el) {
      el.pause();
      el.currentTime = 0;
      el.volume = masterGain ? masterGain.gain.value : 0.6;
      const p = el.play();
      if (p !== undefined) p.catch(e => console.log('Wrong audio error:', e));
    }
  } catch (e) {
    console.log('Error playing wrong audio:', e);
  }
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
    playTick(remainingSeconds);
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
