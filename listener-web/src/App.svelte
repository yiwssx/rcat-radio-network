<script lang="ts">
  type PlaybackStatus = 'idle' | 'connecting' | 'playing' | 'paused' | 'error';
  const STREAM_URL = 'https://radio.rcat.ac.th:8600/main.mp3';
  const COLLEGE_URL = 'https://www.rcat.ac.th/';

  let audioElement: HTMLAudioElement;
  let status = $state<PlaybackStatus>('idle');
  let volume = $state(75);
  let menuOpen = $state(false);

  const isActive = $derived(status === 'playing');
  const statusText = $derived(
    status === 'playing' ? 'กำลังรับฟังสถานี' :
    status === 'connecting' ? 'กำลังเชื่อมต่อสัญญาณ…' :
    status === 'paused' ? 'หยุดเล่นชั่วคราว' :
    status === 'error' ? 'ไม่สามารถรับสัญญาณได้ กรุณาลองอีกครั้ง' :
    'พร้อมรับฟัง กดเล่นเพื่อเริ่มต้น'
  );

  async function togglePlayback() {
    if (!audioElement) return;
    if (status === 'playing' || status === 'connecting') {
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
    volume = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (audioElement) audioElement.volume = volume / 100;
  }
</script>

<svelte:head>
  <meta property="og:title" content="RCAT Radio Network | ฟังวิทยุออนไลน์" />
  <meta property="og:description" content="สถานีวิทยุออนไลน์ วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด" />
</svelte:head>

<a class="skip-link" href="#listen">ข้ามไปยังเครื่องเล่นวิทยุ</a>
<div class="site-shell">
  <header class="topbar">
    <div class="container topbar-inner">
      <a class="institution" href={COLLEGE_URL} target="_blank" rel="noopener noreferrer" aria-label="เว็บไซต์วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด (เปิดแท็บใหม่)">
        <div class="college-mark" aria-hidden="true"><span>วษท.</span><img src="https://www.rcat.ac.th/rcat-logo-128.png" alt="" loading="eager" /></div>
        <span class="institution-name">วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด<small>Roi-Et College of Agriculture and Technology</small></span>
      </a>
      <a class="station-wordmark" href="#home" aria-label="RCAT Radio Network หน้าแรก">
        <svg class="wave-mark" width="42" height="42" viewBox="0 0 44 44" fill="none" aria-hidden="true">
          <rect x="4" y="16" width="5" height="12" rx="2.5" fill="currentColor"/><rect x="12" y="10" width="5" height="24" rx="2.5" fill="currentColor"/><rect x="20" y="4" width="5" height="36" rx="2.5" fill="currentColor"/><rect x="28" y="12" width="5" height="20" rx="2.5" fill="currentColor"/><rect x="36" y="18" width="5" height="8" rx="2.5" fill="currentColor"/>
        </svg>
        <span><strong>RCAT</strong><small>Radio Network</small></span>
      </a>
      <nav class:opened={menuOpen} class="navlinks" aria-label="เมนูหลัก">
        <a class="nav-active" href="#home" onclick={() => menuOpen = false}>หน้าแรก</a>
        <a href="#listen" onclick={() => menuOpen = false}>ฟังวิทยุสด</a>
        <a href="#about" onclick={() => menuOpen = false}>เกี่ยวกับสถานี</a>
        <a href="mailto:saraban@rcat.ac.th" onclick={() => menuOpen = false}>ติดต่อเรา</a>
      </nav>
      <button class="menu-toggle" aria-label={menuOpen ? 'ปิดเมนู' : 'เปิดเมนู'} aria-expanded={menuOpen} onclick={() => menuOpen = !menuOpen}>
        <span></span><span></span><span></span>
      </button>
    </div>
  </header>

  <main id="home">
    <section class="hero" aria-labelledby="hero-title">
  <div class="hero-photo" aria-hidden="true"></div>
  <div class="hero-shade" aria-hidden="true"></div>
  <div class="hero-accent" aria-hidden="true"></div>
  <div class="container hero-content">
    <div class="hero-copy">
      <div class="hero-heading-row">
        <svg class="hero-wave-mark" viewBox="0 0 48 80" width="52" height="81" fill="none" aria-hidden="true"><path d="M24 5v70M12 19v42M36 19v42M3 30v20M45 30v20" stroke="currentColor" stroke-width="6" stroke-linecap="round"/></svg>
        <h1 id="hero-title">RCAT<br /><span>Radio Network</span></h1>
      </div>
      <p class="hero-leading">สถานีวิทยุออนไลน์<br />วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</p>
    </div>
  </div>
  <div class="hero-wave" aria-hidden="true"></div>
</section>

    <section class="container player-wrap" id="listen" aria-label="เครื่องเล่นวิทยุออนไลน์">
  <div class="player-panel">
    <div class="player-station-icon" aria-hidden="true">
      <svg viewBox="0 0 44 42" width="37" height="36" fill="none"><path d="M22 3v36M14 10v22M30 10v22M6 17v8M38 17v8" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg>
      <strong>RCAT</strong><span>RADIO</span>
    </div>
    <div class="player-description">
      <span class="radio-chip">◉ สด · LIVE STREAM</span>
      <h2>RCAT Radio Network</h2>
      <p>สถานีวิทยุออนไลน์ของวิทยาลัย</p>
    </div>
    <button class="play-button" onclick={togglePlayback} aria-label={isActive || status === 'connecting' ? 'หยุดฟังวิทยุ' : 'เริ่มฟังวิทยุ'} title={isActive || status === 'connecting' ? 'หยุดฟัง' : 'ฟังวิทยุสด'}>
      {#if isActive || status === 'connecting'}
       <svg viewBox="0 0 24 24" width="30" height="30" fill="currentColor" aria-hidden="true"><rect x="5" y="3" width="5" height="18" rx="1.5"/><rect x="14" y="3" width="5" height="18" rx="1.5"/></svg>
      {:else}
       <svg viewBox="0 0 24 24" width="30" height="30" fill="currentColor" aria-hidden="true"><path d="M7 4.5a1.5 1.5 0 0 1 2.32-1.26l11.22 7.5a1.5 1.5 0 0 1 0 2.5l-11.22 7.5A1.5 1.5 0 0 1 7 19.5v-15Z"/></svg>
      {/if}
    </button>
    <div class="volume-group">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16 9a5 5 0 0 1 0 6M18 5a9 9 0 0 1 0 14"/></svg>
      <input aria-label="ระดับเสียง" title="ปรับระดับเสียง" type="range" min="0" max="100" step="1" value={volume} oninput={updateVolume} style={`--volume-fill: ${volume}%`} />
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16 9a5 5 0 0 1 0 6M18 5a9 9 0 0 1 0 14"/></svg>
    </div>
    <div class="playback-message" role="status" aria-live="polite">
      <span class:active={status === 'playing'} class:error={status === 'error'} class="status-dot"></span>
      <span>{statusText}</span>
    </div>
  </div>
  <audio bind:this={audioElement} src={STREAM_URL} preload="none" onplaying={() => status = 'playing'} onwaiting={() => { if (status !== 'paused') status = 'connecting'; }} onpause={() => { if (status !== 'error') status = 'paused'; }} onended={() => status = 'error'} onerror={() => status = 'error'}></audio>
</section>

    <section class="container short-links" aria-label="ลิงก์สำคัญ">
  <div class="shortcut-grid">
    <div class="short-link disabled" aria-disabled="true" title="ยังไม่มีตารางรายการเผยแพร่">
      <span class="tile-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="5" y="8" width="22" height="17" rx="3"/><path d="M9 12h14M9 17h8M19 18h4M10 4h12"/></svg></span><strong>ตารางรายการ</strong><small>รอเผยแพร่</small>
    </div>
    <a href="https://www.rcat.ac.th/announcements" target="_blank" rel="noopener noreferrer" class="short-link">
      <span class="tile-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 13h5l15-7v20l-15-7H5v-6Z"/><path d="m9 20 2 8h5l-2-7"/></svg></span><strong>ข่าวประชาสัมพันธ์</strong><small>เว็บไซต์วิทยาลัย ↗</small>
    </a>
    <a href={COLLEGE_URL} target="_blank" rel="noopener noreferrer" class="short-link">
      <span class="tile-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m12 12 12-7v22l-12-7H6v-8h6Z"/><path d="M9 20v7M26 12h4M26 19h4"/></svg></span><strong>กิจกรรมวิทยาลัย</strong><small>ดูข้อมูลเพิ่มเติม ↗</small>
    </a>
    <a href="mailto:saraban@rcat.ac.th" class="short-link">
      <span class="tile-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="12" r="5"/><circle cx="23" cy="13" r="4"/><path d="M2 28v-2c0-6 4-9 9-9s9 3 9 9v2M22 19c5 1 8 3 8 9"/></svg></span><strong>ติดต่อเรา</strong><small>saraban@rcat.ac.th</small>
    </a>
  </div>
  <div class="follow-section">
    <h2>ติดตามเราได้ที่</h2>
    <div class="socials">
      <a aria-label="Facebook วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/profile.php?id=100063746585360">f</a>
      <a aria-label="YouTube วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/@RCAT101">▶</a>
      <a aria-label="TikTok วิทยาลัย" target="_blank" rel="noopener noreferrer" href="https://www.tiktok.com/@rcat_101">♪</a>
      <a aria-label="เว็บไซต์วิทยาลัย" target="_blank" rel="noopener noreferrer" href={COLLEGE_URL}>↗</a>
    </div>
  </div>
</section>

    
  </main>

  <footer class="footer" id="about"><div class="container footer-inner">
  <div><strong>▂▆█▆▂ &nbsp; RCAT Radio Network</strong><span>เสียงความรู้ คู่เกษตรก้าวหน้า เพื่อชุมชนและสังคม</span></div>
  <a href="#listen">♫ รับฟังวิทยุออนไลน์</a>
</div></footer>
</div>
