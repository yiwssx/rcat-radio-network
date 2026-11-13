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
        <a class="nav-active" href="#home" onclick={() => menuOpen = false}>⌂ หน้าแรก</a>
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
          <svg viewBox="0 0 68 55" fill="none" class="cover-icon"><path d="M13 30V23C13 10 22 4 34 4s21 6 21 19v7" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><rect x="6" y="24" width="13" height="22" rx="6" fill="currentColor"/><rect x="49" y="24" width="13" height="22" rx="6" fill="currentColor"/><path d="M34 12v32M27 19v20M41 19v20" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg>
          <strong>RCAT</strong><span>RADIO</span>
        </div>
        <div class="player-description">
          <span class="radio-chip"><span class="chip-broadcast" aria-hidden="true">◉</span> สด</span>
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
          <svg viewBox="0 0 40 40" aria-hidden="true"><rect x="6" y="12" width="28" height="21" rx="4"/><path d="M10 16h20M10 8h20M13 23h10M13 28h6"/></svg>
          <strong>ตารางรายการ</strong>
        </button>
        <a class="short-link" href="https://www.rcat.ac.th/announcements" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 40 40" aria-hidden="true"><path d="M8 18h7L31 9v23L15 23H8z"/><path d="m13 25 3 9h6l-3-9M34 17v8"/></svg>
          <strong>ข่าวประชาสัมพันธ์</strong>
        </a>
        <button class="short-link" onclick={openActivity} title="สถานะข้อมูลกิจกรรมสถานี">
          <svg viewBox="0 0 40 40" aria-hidden="true"><path d="M8 10q6-2 12 2 6-4 12-2v24q-6-3-12 1-6-4-12-1zM20 12v23"/></svg>
          <strong>กิจกรรมสถานี</strong>
        </button>
        <a class="short-link" href="mailto:saraban@rcat.ac.th">
          <svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="14" cy="14" r="6"/><circle cx="29" cy="16" r="5"/><path d="M2 34c0-9 5-13 12-13s12 4 12 13M26 23c7 1 11 4 11 11"/></svg>
          <strong>ติดต่อเรา</strong>
        </a>
      </div>
      <div class="follow-section"><h2>ติดตามเราได้ที่</h2><div class="socials">
        <a class="facebook" aria-label="Facebook วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/profile.php?id=100063746585360">f</a>
        <a class="youtube" aria-label="YouTube วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/@RCAT101">▶</a>
        <a class="tiktok" aria-label="TikTok วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.tiktok.com/@rcat_101">♪</a>
        <a class="website" aria-label="เว็บไซต์วิทยาลัย" target="_blank" rel="noopener noreferrer" href={COLLEGE_URL}>◎</a>
      </div></div>
    </section>
  </main>

  <footer class="footer" id="about">
    <div class="footer-inner">
      <div class="footer-station"><svg viewBox="0 0 54 38" aria-hidden="true"><path d="M27 3v32M18 9v20M36 9v20M9 14v10M45 14v10" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg><strong>RCAT Radio Network</strong></div>
      <span class="footer-claim">เสียงความรู้ คู่เกษตรก้าวหน้า เพื่อชุมชนและสังคม</span>
      <a class="footer-listen" href="#listen">♫ &nbsp;รับฟังได้ทุกที่ ทุกเวลา</a>
    </div>
  </footer>
</div>