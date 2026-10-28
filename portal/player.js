import { resolveStreamUrl } from './stream-url.mjs';

const audio = document.getElementById('audio');
const play = document.getElementById('play');
const volume = document.getElementById('volume');
const track = document.getElementById('track');
const subtitle = document.getElementById('subtitle');
const state = document.getElementById('state');
const error = document.getElementById('error');
const audience = document.getElementById('audience');

let streamUrl = null;
let onAir = false;
audio.volume = .65;

volume.addEventListener('input', () => {
  audio.volume = Math.min(1, Math.max(0, Number(volume.value) / 100));
});

function updatePlayButton() {
  const playing = !audio.paused;
  play.textContent = playing ? 'Ⅱ หยุดฟัง' : '▶ ฟังสด';
  play.setAttribute('aria-pressed', String(playing));
}

function setStatus(online, label) {
  state.classList.toggle('onair', online);
  state.replaceChildren();
  const dot = document.createElement('span');
  dot.className = 'dot';
  dot.setAttribute('aria-hidden', 'true');
  state.append(dot, document.createTextNode(label));
}

function disconnect() {
  if (!audio.paused) audio.pause();
  if (audio.getAttribute('src')) {
    audio.removeAttribute('src');
    audio.load();
  }
  updatePlayButton();
}

play.addEventListener('click', async () => {
  if (!streamUrl || !onAir) return;
  if (!audio.paused) {
    audio.pause();
    return;
  }
  try {
    if (audio.src !== streamUrl) {
      audio.src = streamUrl;
    }
    await audio.play();
    error.textContent = '';
  } catch {
    error.textContent = 'ไม่สามารถเล่นสตรีมได้ กรุณาลองใหม่';
  } finally {
    updatePlayButton();
  }
});

for (const type of ['playing', 'pause', 'ended']) {
  audio.addEventListener(type, updatePlayButton);
}
audio.addEventListener('error', () => {
  error.textContent = 'สัญญาณเสียงขัดข้อง โปรดลองฟังใหม่อีกครั้ง';
  updatePlayButton();
});

async function refresh() {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    let station;
    try {
      const response = await fetch('/api/nowplaying/rcat_radio', {
        cache: 'no-store', signal: controller.signal,
      });
      if (!response.ok) throw new Error('api_unavailable');
      station = await response.json();
    } finally {
      clearTimeout(timer);
    }
    if (station?.station?.shortcode !== 'rcat_radio') {
      throw new Error('wrong_station');
    }
    const live = station.is_online === true;
    const next = live
      ? resolveStreamUrl(station.station.listen_url, window.location.origin)
      : null;
    const changed = next && streamUrl && next !== streamUrl;
    onAir = live;
    streamUrl = next;
    track.textContent = station.now_playing?.song?.title || 'RCAT Radio';
    subtitle.textContent = [
      station.now_playing?.song?.artist,
      station.live?.is_live ? 'Live DJ' : 'AutoDJ / ผังรายการ',
    ].filter(Boolean).join(' • ');
    const listeners = station.listeners?.current;
    audience.textContent = Number.isInteger(listeners) && listeners >= 0
      ? `ผู้ฟังพร้อมกัน ${listeners} คน` : 'จำนวนผู้ฟังยังไม่พร้อมใช้งาน';
    setStatus(live, live ? 'ON AIR' : 'OFF AIR');
    play.disabled = !next;
    if (!next) {
      disconnect();
      error.textContent = live ? 'ไม่พบเส้นทางสตรีมที่อนุญาต' : '';
    } else if (changed && !audio.paused) {
      // Do not silently switch active audio to a different destination.
      disconnect();
      error.textContent = 'เส้นทางสตรีมเปลี่ยน โปรดกดฟังสดอีกครั้ง';
    } else {
      error.textContent = '';
    }
  } catch {
    onAir = false;
    streamUrl = null;
    play.disabled = true;
    disconnect();
    track.textContent = 'รอเชื่อมต่อสถานี';
    subtitle.textContent = 'ยังไม่สามารถอ่านสถานะจาก AzuraCast';
    audience.textContent = '';
    error.textContent = 'การเชื่อมต่อขัดข้อง ระบบจะลองใหม่อัตโนมัติ';
    setStatus(false, 'WAITING');
  }
}

await refresh();
setInterval(refresh, 15000);
