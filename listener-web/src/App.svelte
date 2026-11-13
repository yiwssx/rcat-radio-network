<script lang="ts">
  type PlaybackStatus = 'idle' | 'connecting' | 'playing' | 'paused' | 'error';
  const STREAM_URL = 'https://radio.rcat.ac.th:8600/main.mp3';
  const COLLEGE_URL = 'https://www.rcat.ac.th/';

  let audioElement: HTMLAudioElement;
  let status = $state<PlaybackStatus>('idle');
  let volume = $state(75);
  let menuOpen = $state(false);
  let scheduleNotice = $state(false);
  let activityNotice = $state(false);
  const isPlaying = $derived(status === 'playing');
  const isConnecting = $derived(status === 'connecting');
  const statusText = $derived(
    status === 'playing' ? 'กำลังรับฟัง' :
    status === 'connecting' ? 'กำลังเชื่อมต่อสัญญาณ…' :
    status === 'paused' ? 'หยุดฟังชั่วคราว' :
    status === 'error' ? 'ไม่สามารถรับสัญญาณได้' :
    'พร้อมรับฟัง · กดปุ่มเล่น'
  );

  async function togglePlayback() {
    if (!audioElement) return;
    if (isPlaying || isConnecting) {
      audioElement.pause();
      status = 'paused';
      return;
    }
    status = 'connecting';
    try {
      audioElement.volume = volume / 100;
      await audioElement.play();
    } catch {
      if (status === 'connecting') status = 'error';
    }
  }

  function updateVolume(event: Event) {
    volume = Number((event.currentTarget as HTMLInputElement).value);
    if (audioElement) audioElement.volume = volume / 100;
  }

  function openSchedule() {
    scheduleNotice = !scheduleNotice;
    activityNotice = false;
    menuOpen = false;
  }

  function openActivity() {
    activityNotice = !activityNotice;
    scheduleNotice = false;
  }
</script>

<svelte:head>
  <meta property="og:title" content="RCAT Radio Network | ฟังวิทยุออนไลน์" />
  <meta property="og:description" content="สถานีวิทยุออนไลน์ วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด" />
</svelte:head>

<a href="#listen" class="skip-link">ข้ามไปยังเครื่องเล่นวิทยุ</a>
<div class="site-shell" id="home">
  <header class="topbar">
    <div class="header-inner">
      <a class="institution" href={COLLEGE_URL} target="_blank" rel="noopener noreferrer" aria-label="เว็บไซต์วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด (เปิดแท็บใหม่)">
        <!-- A reference-image crest is a preview fallback only; replace with verified college asset before deployment. -->
        <img class="college-mark" src="https://www.rcat.ac.th/rcat-logo-128.png" alt="" width="68" height="68" />
        <span class="institution-name">วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด<small>Roi-Et College of Agriculture and Technology (RCAT)</small></span>
      </a>
      <a class="station-wordmark" href="#home" aria-label="RCAT Radio Network หน้าแรก">
        <svg class="logo-signal" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M4.9 16.1C1 12.2 1 5.8 4.9 1.9" />
  <path d="M7.8 4.7a6.14 6.14 0 0 0-.8 7.5" />
  <circle cx="12" cy="9" r="2" />
  <path d="M16.2 4.8c2 2 2.26 5.11.8 7.47" />
  <path d="M19.1 1.9a9.96 9.96 0 0 1 0 14.1" />
  <path d="M9.5 18h5" />
  <path d="m8 22 4-11 4 11" />
</svg>

        <span><strong>RCAT</strong><small>Radio Network</small></span>
      </a>
      <nav class:opened={menuOpen} class="navlinks" aria-label="เมนูหลัก">
        <a class="nav-active" href="#home" onclick={() => menuOpen = false}><svg class="home-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" />
  <path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
</svg>
 หน้าแรก</a>
        <button onclick={openSchedule}>ตารางรายการ</button>
        <a href="https://www.rcat.ac.th/announcements" target="_blank" rel="noopener noreferrer" onclick={() => menuOpen = false}>ข่าวสาร</a>
        <a href="#about" onclick={() => menuOpen = false}>เกี่ยวกับสถานี</a>
      </nav>
      <button class="menu-toggle" aria-label={menuOpen ? 'ปิดเมนู' : 'เปิดเมนู'} aria-expanded={menuOpen} onclick={() => menuOpen = !menuOpen}>
        {#if menuOpen}<svg class="menu-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M18 6 6 18" />
  <path d="m6 6 12 12" />
</svg>
{:else}<svg class="menu-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <line x1="4" x2="20" y1="12" y2="12" />
  <line x1="4" x2="20" y1="6" y2="6" />
  <line x1="4" x2="20" y1="18" y2="18" />
</svg>
{/if}
      </button>
    </div>
  </header>

  <main>
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-photo" aria-hidden="true"></div>
      <div class="hero-shade" aria-hidden="true"></div>
      <div class="hero-accent" aria-hidden="true"></div>
      <div class="hero-content">
        <div class="hero-heading-row">
          <svg class="hero-signal" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M2 10v3" />
  <path d="M6 6v11" />
  <path d="M10 3v18" />
  <path d="M14 8v7" />
  <path d="M18 5v13" />
  <path d="M22 10v3" />
</svg>

          <h1 id="hero-title">RCAT<br /><span>Radio Network</span></h1>
        </div>
        <p>สถานีวิทยุออนไลน์<br />วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</p>
      </div>
      <div class="hero-bottom-swoosh" aria-hidden="true"></div>
    </section>

    <section class="player-wrap" id="listen" aria-label="เครื่องเล่นวิทยุออนไลน์">
      <div class="player-panel">
        <div class="player-station-icon" aria-hidden="true">
          <svg class="cover-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3" />
</svg>

          <strong>RCAT</strong><span>RADIO</span>
        </div>
        <div class="player-description">
          <span class="radio-chip"><svg class="chip-broadcast" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9" />
  <path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5" />
  <circle cx="12" cy="12" r="2" />
  <path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5" />
  <path d="M19.1 4.9C23 8.8 23 15.1 19.1 19" />
</svg>
 สด</span>
          <p class="playing-label">สตรีมวิทยุออนไลน์</p>
          <h2>RCAT Radio Network</h2>
        </div>
        <div class="player-play-area">
          <button class="play-button" onclick={togglePlayback} aria-label={isPlaying || isConnecting ? 'หยุดฟังวิทยุ' : 'เริ่มฟังวิทยุ'} title={isPlaying || isConnecting ? 'หยุดฟัง' : 'ฟังวิทยุสด'}>
            {#if isPlaying || isConnecting}
              <svg class="player-control-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <rect x="14" y="4" width="4" height="16" rx="1" />
  <rect x="6" y="4" width="4" height="16" rx="1" />
</svg>

            {:else}
              <svg class="player-control-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <polygon points="6 3 20 12 6 21 6 3" />
</svg>

            {/if}
          </button>
        </div>
        <div class="volume-group">
          <svg class="volume-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" />
  <path d="M16 9a5 5 0 0 1 0 6" />
</svg>

          <input aria-label="ระดับเสียง" title="ปรับระดับเสียง" type="range" min="0" max="100" step="1" value={volume} oninput={updateVolume} style={`--volume-fill: ${volume}%`} />
          <svg class="volume-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" />
  <path d="M16 9a5 5 0 0 1 0 6" />
  <path d="M19.364 18.364a9 9 0 0 0 0-12.728" />
</svg>

        </div>
        <div class="playback-message" role="status" aria-live="polite"><span class:active={isPlaying} class:error={status === 'error'} class="status-dot"></span><span>{statusText}</span></div>
      </div>
      <audio bind:this={audioElement} src={STREAM_URL} preload="none"
        onplaying={() => status = 'playing'}
        onwaiting={() => { if (status !== 'paused') status = 'connecting'; }}
        onpause={() => { if (status !== 'error') status = 'paused'; }}
        onended={() => status = 'error'}
        onerror={() => status = 'error'}></audio>
      {#if scheduleNotice || activityNotice}<div class="schedule-notice" role="status">{scheduleNotice ? 'ยังไม่มีตารางรายการเผยแพร่ในขณะนี้' : 'ยังไม่มีข้อมูลกิจกรรมสถานีเผยแพร่ในขณะนี้'} <button onclick={() => {scheduleNotice = false; activityNotice = false;}}>ปิด</button></div>{/if}
    </section>

    <section class="short-links" aria-label="ลิงก์สำคัญ">
      <div class="shortcut-grid">
        <button class="short-link" onclick={openSchedule} title="ดูสถานะตารางรายการ">
          <svg class="shortcut-icon radio-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M5 16v2" />
  <path d="M19 16v2" />
  <rect width="20" height="8" x="2" y="8" rx="2" />
  <path d="M18 12h.01" />
</svg>

          <strong>ตารางรายการ</strong>
        </button>
        <a class="short-link" href="https://www.rcat.ac.th/announcements" target="_blank" rel="noopener noreferrer">
          <svg class="shortcut-icon megaphone-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="m3 11 18-5v12L3 14v-3z" />
  <path d="M11.6 16.8a3 3 0 1 1-5.8-1.6" />
</svg>

          <strong>ข่าวประชาสัมพันธ์</strong>
        </a>
        <button class="short-link" onclick={openActivity} title="สถานะข้อมูลกิจกรรมสถานี">
          <svg class="shortcut-icon note-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M9 18V5l12-2v13" />
  <circle cx="6" cy="18" r="3" />
  <circle cx="18" cy="16" r="3" />
</svg>

          <strong>กิจกรรมสถานี</strong>
        </button>
        <a class="short-link" href="mailto:saraban@rcat.ac.th">
          <svg class="shortcut-icon team-icon" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M18 21a8 8 0 0 0-16 0" />
  <circle cx="10" cy="8" r="5" />
  <path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3" />
</svg>

          <strong>ติดต่อเรา</strong>
        </a>
      </div>
      <div class="follow-section"><h2>ติดตามเราได้ที่</h2><div class="socials">
        <a class="facebook" aria-label="Facebook วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/profile.php?id=100063746585360" title="Facebook"><svg class="social-generic-icon facebook-mark" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M18 21a8 8 0 0 0-16 0" />
  <circle cx="10" cy="8" r="5" />
  <path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3" />
</svg>
12940
        <a class="youtube" aria-label="YouTube วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/@RCAT101" title="Youtube"><svg class="social-generic-icon youtube-mark" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <circle cx="12" cy="12" r="10" />
  <polygon points="10 8 16 12 10 16 10 8" />
</svg>
13542
        <a class="tiktok" aria-label="TikTok วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.tiktok.com/@rcat_101" title="Tiktok"><svg class="social-generic-icon tiktok-mark" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M9 18V5l12-2v13" />
  <circle cx="6" cy="18" r="3" />
  <circle cx="18" cy="16" r="3" />
</svg>
14070
        <a class="website" aria-label="เว็บไซต์วิทยาลัย" target="_blank" rel="noopener noreferrer" href={COLLEGE_URL}><svg class="social-generic-icon website-mark" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <circle cx="12" cy="12" r="10" />
  <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
  <path d="M2 12h20" />
</svg>
</a>
      </div></div>
    </section>
  </main>

  <footer class="footer" id="about">
    <div class="footer-inner">
      <div class="footer-station"><svg class="footer-signal" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M2 10v3" />
  <path d="M6 6v11" />
  <path d="M10 3v18" />
  <path d="M14 8v7" />
  <path d="M18 5v13" />
  <path d="M22 10v3" />
</svg>
<strong>RCAT Radio Network</strong></div>
      <span class="footer-claim">เสียงความรู้ คู่เกษตรก้าวหน้า เพื่อชุมชนและสังคม</span>
      <a class="footer-listen" href="#listen"><svg class="footer-headphones" aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3" />
</svg>
 รับฟังได้ทุกที่ ทุกเวลา</a>
    </div>
  </footer>
</div>