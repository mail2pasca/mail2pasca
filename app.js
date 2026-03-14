// ─── Ball Speed Detector ────────────────────────────────────────────────────

const video       = document.getElementById('video');
const overlay     = document.getElementById('overlay');
const ctx         = overlay.getContext('2d');
const startBtn    = document.getElementById('startBtn');
const stopBtn     = document.getElementById('stopBtn');
const speedVal    = document.getElementById('speedVal');
const peakVal     = document.getElementById('peakVal');
const speedUnit   = document.getElementById('speedUnit');
const statusDot   = document.getElementById('statusDot');
const resetPeakBtn  = document.getElementById('resetPeakBtn');
const speedsList    = document.getElementById('speedsList');
const speedsEmpty   = document.getElementById('speedsEmpty');
const pickColorBtn= document.getElementById('pickColorBtn');
const ballColorEl = document.getElementById('ballColor');
const toleranceEl = document.getElementById('tolerance');
const toleranceValEl = document.getElementById('toleranceVal');
const minSizeEl   = document.getElementById('minSize');
const realWidthEl = document.getElementById('realWidth');
const pixelWidthEl= document.getElementById('pixelWidth');
const unitSelect  = document.getElementById('unitSelect');

// ─── State ──────────────────────────────────────────────────────────────────
let stream = null;
let animId = null;
let picking = false;

// Ball tracking history
const HISTORY_FRAMES = 6;       // frames to average speed over
const TRAIL_LENGTH   = 30;      // trail dots
let positions = [];             // [{x, y, t}]
let trail     = [];             // [{x, y}]
let peakSpeed = null;
let topSpeeds = [];           // sorted desc, max 10 entries
const TOP_SPEEDS_MAX = 10;
// Minimum speed delta to record a new throw (avoids flooding list with near-identical readings)
const MIN_RECORD_DELTA = 0.5;

// Hidden processing canvas (full res)
const procCanvas = document.createElement('canvas');
const procCtx    = procCanvas.getContext('2d', { willReadFrequently: true });

// ─── Utilities ───────────────────────────────────────────────────────────────

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

function colorDistance(r1, g1, b1, r2, g2, b2) {
  // Weighted Euclidean in RGB — good enough for live color tracking
  const dr = r1 - r2, dg = g1 - g2, db = b1 - b2;
  return Math.sqrt(2 * dr * dr + 4 * dg * dg + 3 * db * db);
}

function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
}

// ─── Speed conversion ────────────────────────────────────────────────────────

function pixelsPerSecToSpeed(pps) {
  const realW = parseFloat(realWidthEl.value) || 30;   // cm
  const pixW  = parseFloat(pixelWidthEl.value) || 100; // px
  const cmPerPx = realW / pixW;                        // cm/px
  const cmPerSec = pps * cmPerPx;                      // cm/s
  const mPerSec  = cmPerSec / 100;

  const unit = unitSelect.value;
  if (unit === 'kmh') return { val: mPerSec * 3.6,    label: 'km/h' };
  if (unit === 'mph') return { val: mPerSec * 2.237,  label: 'mph'  };
  return                      { val: mPerSec,          label: 'm/s'  };
}

// ─── Top speeds ──────────────────────────────────────────────────────────────

// Track the last "throw peak" — we record a speed when it starts dropping
let lastSpeed     = 0;
let throwPeak     = 0;
let throwRecorded = false;

function maybeRecordThrow(speed) {
  if (speed > throwPeak) {
    throwPeak     = speed;
    throwRecorded = false;
  } else if (!throwRecorded && throwPeak > MIN_RECORD_DELTA && speed < throwPeak * 0.75) {
    // Speed dropped 25% from peak → treat as end of throw, record peak
    addTopSpeed(throwPeak);
    throwRecorded = true;
    throwPeak     = 0;
  }
  lastSpeed = speed;
}

function addTopSpeed(speed) {
  topSpeeds.push(speed);
  topSpeeds.sort((a, b) => b - a);
  if (topSpeeds.length > TOP_SPEEDS_MAX) topSpeeds.length = TOP_SPEEDS_MAX;
  renderTopSpeeds();
}

function renderTopSpeeds() {
  const unit = speedUnit.textContent;
  speedsList.innerHTML = '';

  if (topSpeeds.length === 0) {
    speedsList.innerHTML = '<p class="speeds-empty" id="speedsEmpty">No throws recorded yet — start the camera and throw!</p>';
    return;
  }

  const medals = ['🥇', '🥈', '🥉'];
  const tierClass = ['gold', 'silver', 'bronze'];

  topSpeeds.forEach((s, i) => {
    const div = document.createElement('div');
    div.className = 'leaderboard-entry' + (i < 3 ? ` ${tierClass[i]}` : '');
    div.innerHTML = `
      <span class="lb-rank">${medals[i] ?? `#${i + 1}`}</span>
      <span class="lb-speed">${s.toFixed(1)}</span>
      <span class="lb-unit">${unit}</span>
    `;
    speedsList.appendChild(div);
  });
}

// ─── Ball detection ──────────────────────────────────────────────────────────

function detectBall(imageData, targetR, targetG, targetB, tolerance, minSize) {
  const { data, width, height } = imageData;
  const maxDist = tolerance * 6; // scale tolerance to the weighted metric range

  // Downscale search by stepping every 2 pixels for speed
  let sumX = 0, sumY = 0, count = 0;

  for (let y = 0; y < height; y += 2) {
    for (let x = 0; x < width; x += 2) {
      const i = (y * width + x) * 4;
      const r = data[i], g = data[i + 1], b = data[i + 2];
      const dist = colorDistance(r, g, b, targetR, targetG, targetB);
      if (dist < maxDist) {
        sumX += x; sumY += y; count++;
      }
    }
  }

  if (count < minSize * minSize / 4) return null; // not enough matching pixels

  return {
    x: sumX / count,
    y: sumY / count,
    size: Math.sqrt(count) * 2,
  };
}

// ─── Main detection loop ─────────────────────────────────────────────────────

function processFrame() {
  if (!stream) return;

  const vw = video.videoWidth;
  const vh = video.videoHeight;
  if (!vw || !vh) { animId = requestAnimationFrame(processFrame); return; }

  // Sync canvas sizes
  if (procCanvas.width !== vw || procCanvas.height !== vh) {
    procCanvas.width = vw;
    procCanvas.height = vh;
  }
  if (overlay.width !== vw || overlay.height !== vh) {
    overlay.width = vw;
    overlay.height = vh;
  }

  // Draw video to hidden canvas & grab pixels
  procCtx.drawImage(video, 0, 0, vw, vh);
  const imageData = procCtx.getImageData(0, 0, vw, vh);

  const target    = hexToRgb(ballColorEl.value);
  const tolerance = parseInt(toleranceEl.value);
  const minSize   = parseInt(minSizeEl.value);

  const det = detectBall(imageData, target.r, target.g, target.b, tolerance, minSize);

  // Clear overlay
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  if (det) {
    const now = performance.now();

    // Store position
    positions.push({ x: det.x, y: det.y, t: now });
    if (positions.length > HISTORY_FRAMES) positions.shift();

    trail.push({ x: det.x, y: det.y });
    if (trail.length > TRAIL_LENGTH) trail.shift();

    // Compute speed from oldest to newest position
    let speed = 0;
    if (positions.length >= 2) {
      const oldest = positions[0];
      const newest = positions[positions.length - 1];
      const dx = newest.x - oldest.x;
      const dy = newest.y - oldest.y;
      const dt = (newest.t - oldest.t) / 1000; // seconds
      if (dt > 0) {
        const pixelSpeed = Math.sqrt(dx * dx + dy * dy) / dt;
        const converted  = pixelsPerSecToSpeed(pixelSpeed);
        speed = converted.val;
        speedUnit.textContent = converted.label;
      }
    }

    // Update displays
    speedVal.textContent = speed.toFixed(1);
    if (peakSpeed === null || speed > peakSpeed) {
      peakSpeed = speed;
      peakVal.textContent = peakSpeed.toFixed(1);
    }

    maybeRecordThrow(speed);

    statusDot.className = 'status-dot tracking';

    // Draw trail
    for (let i = 0; i < trail.length; i++) {
      const alpha = (i / trail.length) * 0.7;
      const r = 2 + (i / trail.length) * 4;
      ctx.beginPath();
      ctx.arc(trail[i].x, trail[i].y, r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(79, 195, 247, ${alpha})`;
      ctx.fill();
    }

    // Draw detection circle
    ctx.beginPath();
    ctx.arc(det.x, det.y, det.size / 2, 0, Math.PI * 2);
    ctx.strokeStyle = '#4fc3f7';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Draw crosshair
    const cs = det.size / 2 + 8;
    ctx.strokeStyle = 'rgba(79, 195, 247, 0.8)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(det.x - cs, det.y); ctx.lineTo(det.x + cs, det.y);
    ctx.moveTo(det.x, det.y - cs); ctx.lineTo(det.x, det.y + cs);
    ctx.stroke();

    // Speed label near ball
    if (speed > 0.5) {
      const converted = pixelsPerSecToSpeed(0); // just get unit label
      ctx.font = 'bold 14px Segoe UI, sans-serif';
      ctx.fillStyle = '#4fc3f7';
      ctx.textAlign = 'center';
      ctx.fillText(`${speed.toFixed(1)} ${speedUnit.textContent}`, det.x, det.y - det.size / 2 - 10);
    }

  } else {
    // Ball lost — if a throw was in progress, record its peak now
    if (throwPeak > MIN_RECORD_DELTA && !throwRecorded) {
      addTopSpeed(throwPeak);
      throwRecorded = true;
      throwPeak = 0;
    }
    statusDot.className = 'status-dot active';
  }

  animId = requestAnimationFrame(processFrame);
}

// ─── Color picking from video ─────────────────────────────────────────────────

overlay.addEventListener('click', (e) => {
  if (!picking || !stream) return;

  const rect = overlay.getBoundingClientRect();
  const scaleX = overlay.width  / rect.width;
  const scaleY = overlay.height / rect.height;
  const px = Math.round((e.clientX - rect.left) * scaleX);
  const py = Math.round((e.clientY - rect.top)  * scaleY);

  // Sample a 7x7 area and average colour
  const sample = procCtx.getImageData(Math.max(0, px - 3), Math.max(0, py - 3), 7, 7);
  let sr = 0, sg = 0, sb = 0;
  const n = sample.data.length / 4;
  for (let i = 0; i < sample.data.length; i += 4) {
    sr += sample.data[i]; sg += sample.data[i + 1]; sb += sample.data[i + 2];
  }
  const hex = rgbToHex(Math.round(sr / n), Math.round(sg / n), Math.round(sb / n));
  ballColorEl.value = hex;

  // Flash on overlay where picked
  ctx.save();
  ctx.beginPath();
  ctx.arc(px, py, 16, 0, Math.PI * 2);
  ctx.strokeStyle = '#ffb74d';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.restore();

  picking = false;
  pickColorBtn.textContent = 'Click on Ball in Video';
  pickColorBtn.classList.remove('active');
  overlay.style.cursor = 'default';
});

// ─── Controls ────────────────────────────────────────────────────────────────

startBtn.addEventListener('click', async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    video.srcObject = stream;
    await video.play();

    startBtn.style.display = 'none';
    stopBtn.style.display  = '';
    statusDot.className = 'status-dot active';

    animId = requestAnimationFrame(processFrame);
  } catch (err) {
    alert('Could not access camera: ' + err.message);
  }
});

stopBtn.addEventListener('click', () => {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  if (animId) { cancelAnimationFrame(animId); animId = null; }
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  startBtn.style.display = '';
  stopBtn.style.display  = 'none';
  statusDot.className = 'status-dot';
  speedVal.textContent = '--';
  positions = [];
  trail = [];
});

resetPeakBtn.addEventListener('click', () => {
  peakSpeed = null;
  peakVal.textContent = '--';
  topSpeeds = [];
  throwPeak = 0;
  throwRecorded = false;
  lastSpeed = 0;
  renderTopSpeeds();
});

pickColorBtn.addEventListener('click', () => {
  if (!stream) { alert('Start the camera first.'); return; }
  picking = !picking;
  if (picking) {
    pickColorBtn.textContent = '→ Click on the ball in video';
    pickColorBtn.classList.add('active');
    overlay.style.cursor = 'crosshair';
  } else {
    pickColorBtn.textContent = 'Click on Ball in Video';
    pickColorBtn.classList.remove('active');
    overlay.style.cursor = 'default';
  }
});

toleranceEl.addEventListener('input', () => {
  toleranceValEl.textContent = toleranceEl.value;
});

unitSelect.addEventListener('change', () => {
  peakSpeed = null;
  peakVal.textContent = '--';
  speedVal.textContent = '--';
  positions = [];
  topSpeeds = [];
  throwPeak = 0;
  throwRecorded = false;
  renderTopSpeeds();
});
