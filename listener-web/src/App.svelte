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
        <img class="college-mark" src="/images/crest-reference.svg" alt="" width="68" height="68" />
        <span class="institution-name">วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด<small>Roi-Et College of Agriculture and Technology (RCAT)</small></span>
      </a>
      <a class="station-wordmark" href="#home" aria-label="RCAT Radio Network หน้าแรก">
        <svg class="logo-signal" viewBox="0 0 50 58" fill="none" aria-hidden="true">
          <circle cx="25" cy="22" r="5" fill="currentColor"/>
          <path d="M25 30v20M14 14c-7 8-7 18 0 26M36 14c7 8 7 18 0 26M7 6c-13 17-13 29 0 42M43 6c13 17 13 29 0 42" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
        </svg>
        <span><strong>RCAT</strong><small>Radio Network</small></span>
      </a>
      <nav class:opened={menuOpen} class="navlinks" aria-label="เมนูหลัก">
        <a class="nav-active" href="#home" onclick={() => menuOpen = false}><svg class="home-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M2 10.7 12 2.7l10 8v2.6l-2-1.6V21h-6v-6h-4v6H4v-9.3L2 13.3z"/></svg> หน้าแรก</a>
        <button onclick={openSchedule}>ตารางรายการ</button>
        <a href="https://www.rcat.ac.th/announcements" target="_blank" rel="noopener noreferrer" onclick={() => menuOpen = false}>ข่าวสาร</a>
        <a href="#about" onclick={() => menuOpen = false}>เกี่ยวกับสถานี</a>
      </nav>
      <button class="menu-toggle" aria-label={menuOpen ? 'ปิดเมนู' : 'เปิดเมนู'} aria-expanded={menuOpen} onclick={() => menuOpen = !menuOpen}>
        <span></span><span></span><span></span>
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
          <svg class="hero-signal" viewBox="0 0 54 98" aria-hidden="true">
            <path d="M27 6v86M14 23v52M40 23v52M3 39v20M51 39v20" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
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
          <svg viewBox="0 0 68 58" fill="none" class="cover-icon" aria-hidden="true"><path d="M11 31v-6C11 12 21 4 34 4s23 8 23 21v6" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><rect x="4" y="27" width="14" height="23" rx="6" fill="currentColor"/><rect x="50" y="27" width="14" height="23" rx="6" fill="currentColor"/><circle cx="34" cy="29" r="3" fill="currentColor"/><path d="M34 33v18M27 20a12 12 0 0 0 0 18M41 20a12 12 0 0 1 0 18M21 15a20 20 0 0 0 0 27M47 15a20 20 0 0 1 0 27" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>
          <strong>RCAT</strong><span>RADIO</span>
        </div>
        <div class="player-description">
          <span class="radio-chip"><svg class="chip-broadcast" viewBox="0 0 28 28" fill="none" aria-hidden="true"><circle cx="14" cy="14" r="3" fill="currentColor"/><path d="M14 18v7M8 8a9 9 0 0 0 0 12M20 8a9 9 0 0 1 0 12M4 4a15 15 0 0 0 0 20M24 4a15 15 0 0 1 0 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg> สด</span>
          <p class="playing-label">สตรีมวิทยุออนไลน์</p>
          <h2>RCAT Radio Network</h2>
        </div>
        <div class="player-play-area">
          <button class="play-button" onclick={togglePlayback} aria-label={isPlaying || isConnecting ? 'หยุดฟังวิทยุ' : 'เริ่มฟังวิทยุ'} title={isPlaying || isConnecting ? 'หยุดฟัง' : 'ฟังวิทยุสด'}>
            {#if isPlaying || isConnecting}
              <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><rect x="5" y="3.5" width="5" height="17" rx="1.5"/><rect x="14" y="3.5" width="5" height="17" rx="1.5"/></svg>
            {:else}
              <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M7 4.5c0-1.4 1.5-2.3 2.7-1.6l11 7c1.2.8 1.2 2.4 0 3.2l-11 7C8.5 20.8 7 20 7 18.5v-14Z"/></svg>
            {/if}
          </button>
        </div>
        <div class="volume-group">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16 9a5 5 0 0 1 0 6"/></svg>
          <input aria-label="ระดับเสียง" title="ปรับระดับเสียง" type="range" min="0" max="100" step="1" value={volume} oninput={updateVolume} style={`--volume-fill: ${volume}%`} />
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16 9a5 5 0 0 1 0 6M18 5a9 9 0 0 1 0 14"/></svg>
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
          <svg viewBox="0 0 48 48" aria-hidden="true" class="shortcut-icon radio-icon"><path d="M9 15.5h30a4 4 0 0 1 4 4v21a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4v-21a4 4 0 0 1 4-4Z"/><path d="M10 15 35 4M9 23h29M12 31h15M12 36h9"/><circle cx="35" cy="33" r="4.5"/></svg>
          <strong>ตารางรายการ</strong>
        </button>
        <a class="short-link" href="https://www.rcat.ac.th/announcements" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 48 48" aria-hidden="true" class="shortcut-icon megaphone-icon"><path d="M7 19h9l20-10v30L16 29H7a4 4 0 0 1-4-4v-2a4 4 0 0 1 4-4Z" fill="currentColor" stroke="none"/><path d="m14 29 3 12h9l-5-11" fill="currentColor" stroke="none"/><path d="M40 17q6 7 0 14M42 10q11 13 0 28" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/></svg>
          <strong>ข่าวประชาสัมพันธ์</strong>
        </a>
        <button class="short-link" onclick={openActivity} title="สถานะข้อมูลกิจกรรมสถานี">
          <svg viewBox="0 0 48 48" aria-hidden="true" class="shortcut-icon note-icon"><path d="M17 11 39 6v27.3c0 5.2-3.9 8.9-10.2 8.9-4.6 0-8-2.5-8-6.3 0-3.9 4-7 9.1-7 1.7 0 3 .2 4.3.7V17.5l-12.7 3v17.1c0 5.3-4 8.7-10.3 8.7-4.3 0-7.2-2.5-7.2-6.1 0-4.5 4.3-7.4 9.2-7.4 1.4 0 2.6.1 3.8.5V11Z" fill="currentColor" stroke="none"/></svg>
          <strong>กิจกรรมสถานี</strong>
        </button>
        <a class="short-link" href="mailto:saraban@rcat.ac.th">
          <svg viewBox="0 0 48 48" aria-hidden="true" class="shortcut-icon team-icon"><circle cx="24" cy="12" r="7" fill="currentColor" stroke="none"/><circle cx="10.5" cy="18" r="5.5" fill="currentColor" stroke="none"/><circle cx="37.5" cy="18" r="5.5" fill="currentColor" stroke="none"/><path d="M10 40v-7c0-8 5-13 14-13s14 5 14 13v7H10Z" fill="currentColor" stroke="none"/><path d="M2 40v-8c0-4 3-7 8-8M46 40v-8c0-4-3-7-8-8" stroke="currentColor" stroke-width="5" stroke-linecap="round" fill="none"/></svg>
          <strong>ติดต่อเรา</strong>
        </a>
      </div>
      <div class="follow-section"><h2>ติดตามเราได้ที่</h2><div class="socials">
        <a class="facebook" aria-label="Facebook วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/profile.php?id=100063746585360"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M14.4 22V13.1h3l.5-3.6h-3.5V7.2c0-1 .3-1.7 1.8-1.7H18V2.2c-.4-.1-1.6-.2-2.9-.2-3 0-5.1 1.8-5.1 5.2v2.3H7v3.6h3V22h4.4Z"/></svg></a>
        <a class="youtube" aria-label="YouTube วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/@RCAT101"><svg viewBox="0 0 28 28" aria-hidden="true"><rect x="2" y="6" width="24" height="16" rx="5" fill="currentColor"/><path d="m12 10 8 4-8 4z" fill="#f70e22"/></svg></a>
        <a class="tiktok" aria-label="TikTok วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.tiktok.com/@rcat_101"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="M19 4v16a6 6 0 1 1-5-6" stroke="#25f4ee" stroke-width="5" stroke-linecap="round" fill="none" transform="translate(-1 1)"/><path d="M19 4v16a6 6 0 1 1-5-6" stroke="#fe2c55" stroke-width="5" stroke-linecap="round" fill="none" transform="translate(1 -1)"/><path d="M19 4v16a6 6 0 1 1-5-6M19 4c1 6 4 8 10 8" stroke="#fff" stroke-width="5" stroke-linecap="round" fill="none"/></svg></a>
        <a class="website" aria-label="เว็บไซต์วิทยาลัย" target="_blank" rel="noopener noreferrer" href={COLLEGE_URL}><svg viewBox="0 0 28 28" aria-hidden="true" fill="none"><circle cx="14" cy="14" r="10.5" stroke="currentColor" stroke-width="1.7"/><ellipse cx="14" cy="14" rx="4.1" ry="10.5" stroke="currentColor" stroke-width="1.4"/><path d="M4 14h20M6 9.6h16M6 18.4h16" stroke="currentColor" stroke-width="1.4"/></svg></a>
      </div></div>
    </section>
  </main>

  <footer class="footer" id="about">
    <div class="footer-inner">
      <div class="footer-station"><svg viewBox="0 0 54 38" aria-hidden="true"><path d="M27 3v32M18 9v20M36 9v20M9 14v10M45 14v10" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg><strong>RCAT Radio Network</strong></div>
      <span class="footer-claim">เสียงความรู้ คู่เกษตรก้าวหน้า เพื่อชุมชนและสังคม</span>
      <a class="footer-listen" href="#listen"><svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M5 18v-4a11 11 0 0 1 22 0v4" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/><rect x="2" y="16" width="7" height="12" rx="2.5" fill="currentColor"/><rect x="23" y="16" width="7" height="12" rx="2.5" fill="currentColor"/></svg> รับฟังได้ทุกที่ ทุกเวลา</a>
    </div>
  </footer>
</div>