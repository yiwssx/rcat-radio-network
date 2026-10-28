import { resolveStreamUrl } from './stream-url.mjs';

const player = document.getElementById('audio');
const play = document.getElementById('play');
const track = document.getElementById('track');
const subtitle = document.getElementById('subtitle');
const state = document.getElementById('state');
const error = document.getElementById('error');

let streamUrl = null;
player.volume = .65;
document.getElementById('volume').addEventListener('input', event => {
  player.volume = Number(event.target.value) / 100;
});

play.addEventListener('click', async () => {
  if (!streamUrl) return;
  if (!player.paused) {
    player.pause();
    play.textContent = '▶ ฟังสด';
    return;
  }
  try {
    if (player.src !== streamUrl) player.src = streamUrl;
    await player.play();
    play.textContent = 'Ⅱ หยุดฟัง';
    error.textContent = '';
  } catch {
    error.textContent = 'เล่นเสียงไม่ได้ ตรวจสอบสถานีและเส้นทางสตรีม';
    play.textContent = '▶ ฟังสด';
  }
});
player.addEventListener('error', () => {
  error.textContent = 'การเชื่อมต่อเสียงขัดข้อง';
  play.textContent = '▶ ฟังสด';
});

function setOnline(online, label) {
  state.classList.toggle('onair', online);
  state.textContent = '';
  const dot = document.createElement('span');
  dot.className = 'dot';
  state.appendChild(dot);
  state.appendChild(document.createTextNode(label));
}

async function refresh() {
  try {
    const response = await fetch('/api/nowplaying/rcat_radio', { cache: 'no-store' });
    if (!response.ok) throw new Error('API HTTP ' + response.status);
    const station = await response.json();
    if (station?.station?.shortcode !== 'rcat_radio') throw new Error('ยังไม่ได้สร้างสถานี RCAT');
    const live = Boolean(station.is_online);
    const song = station.now_playing?.song;
    track.textContent = song?.title || 'RCAT Radio';
    subtitle.textContent = [
      song?.artist,
      station.live?.is_live ? 'Live DJ' : 'AutoDJ / ผังรายการ'
    ].filter(Boolean).join(' • ');
    setOnline(live, live ? 'ON AIR' : 'OFF AIR / SETUP');
    const nextStream = resolveStreamUrl(station.station.listen_url, window.location.origin);
    streamUrl = live ? nextStream : null;
    play.disabled = !streamUrl;
    if (live && !nextStream) {
      error.textContent = 'เส้นทางเสียงของสถานีไม่ตรงกับค่า Proxy ที่ตั้งไว้';
    } else if (!live) {
      error.textContent = '';
    }
  } catch (err) {
    streamUrl = null;
    play.disabled = true;
    track.textContent = 'รอการตั้งค่า AzuraCast';
    subtitle.textContent = String(err.message || err);
    setOnline(false, 'WAITING');
  }
}

await refresh();
setInterval(refresh, 15000);
