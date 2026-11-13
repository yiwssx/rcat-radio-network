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
      if (audioElement.paused) status = 'error';
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
        <a href={COLLEGE_URL} target="_blank" rel="noopener noreferrer" onclick={() => menuOpen = false}>เว็บไซต์วิทยาลัย ↗</a>
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
      <div class="container hero-content">
        <div class="hero-copy">
          <div class="eyebrow"><span class="signal-dot" aria-hidden="true"></span> RCAT RADIO NETWORK</div>
          <h1 id="hero-title">เสียงดี ๆ <span>จาก RCAT</span></h1>
          <p class="hero-leading">สถานีวิทยุออนไลน์<br />วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</p>
          <div class="hero-tagline"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v18M8 7a7 7 0 0 0 0 10M16 7a7 7 0 0 1 0 10M4 3a13 13 0 0 0 0 18M20 3a13 13 0 0 1 0 18"/></svg> เสียงเพื่อการเรียนรู้ เกษตร นวัตกรรม และชุมชน</div>
        </div>
        <div class="hero-illustration" aria-hidden="true">
          <div class="disc disc-outside"></div><div class="disc disc-inside"></div>
          <svg class="radio-headset" viewBox="0 0 250 265" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M41 133V116C41 69 78 27 125 27S209 69 209 116V133" stroke="#e8f5ed" stroke-width="22" stroke-linecap="round" />
            <path d="M41 133V116C41 69 78 27 125 27S209 69 209 116V133" stroke="#183b2b" stroke-width="11" stroke-linecap="round" />
            <rect x="19" y="115" width="45" height="86" rx="19" fill="#164c34" stroke="#d2eed7" stroke-width="6" />
            <rect x="186" y="115" width="45" height="86" rx="19" fill="#164c34" stroke="#d2eed7" stroke-width="6" />
            <rect x="97" y="96" width="56" height="103" rx="28" fill="#f5faf1" stroke="#184d32" stroke-width="5" />
            <rect x="108" y="103" width="34" height="91" rx="17" fill="#93aa9b" />
            <path d="M125 201V236M94 236H156" stroke="#d8ece1" stroke-width="9" stroke-linecap="round" />
            <path d="M84 169C84 209 98 216 125 216C152 216 166 209 166 169" stroke="#e8f5ed" stroke-width="8" stroke-linecap="round" />
            <path d="M114 116V181M125 113V181M136 116V181" stroke="#ecf3e9" stroke-width="3" opacity="0.5" />
          </svg>
        </div>
      </div>
      <div class="hero-wave" aria-hidden="true"></div>
    </section>

    <section class="container player-wrap" id="listen" aria-labelledby="player-heading">
      <div class="player-panel">
        <div class="player-station-icon" aria-hidden="true"><svg viewBox="0 0 44 44" width="36" height="36" fill="none"><path d="M22 9v26M15 14v16M29 14v16M8 18v8M36 18v8" stroke="currentColor" stroke-width="5" stroke-linecap="round" /></svg><span>RCAT<br />RADIO</span></div>
        <div class="player-description">
          <span class="radio-chip"><span></span> สตรีมวิทยุสด</span>
          <h2 id="player-heading">RCAT Radio Network</h2>
          <p>วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</p>
        </div>
        <button class="play-button" onclick={togglePlayback} aria-label={isActive || status === 'connecting' ? 'หยุดฟังวิทยุ' : 'เริ่มฟังวิทยุ'} title={isActive || status === 'connecting' ? 'หยุดฟัง' : 'ฟังวิทยุสด'}>
          {#if isActive || status === 'connecting'}
            <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden="true"><rect x="5" y="4" width="5" height="16" rx="1.5"/><rect x="14" y="4" width="5" height="16" rx="1.5"/></svg>
          {:else}
            <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden="true"><path d="M7 4.5a1.5 1.5 0 0 1 2.32-1.26l11.22 7.5a1.5 1.5 0 0 1 0 2.5l-11.22 7.5A1.5 1.5 0 0 1 7 19.5v-15Z"/></svg>
          {/if}
        </button>
        <div class="volume-group">
          <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M18 6a9 9 0 0 1 0 12"/></svg>
          <input aria-label="ระดับเสียง" title="ปรับระดับเสียง" type="range" min="0" max="100" step="1" value={volume} oninput={updateVolume} style={`--volume-fill: ${volume}%`} />
          <span class="volume-percentage" aria-hidden="true">{volume}%</span>
        </div>
        <div class="playback-message" role="status" aria-live="polite">
          <span class:active={status === 'playing'} class:error={status === 'error'} class="status-dot"></span>
          <span>{statusText}</span>
        </div>
      </div>
      <audio bind:this={audioElement} src={STREAM_URL} preload="none" onplaying={() => status = 'playing'} onwaiting={() => { if (status !== 'paused') status = 'connecting'; }} onpause={() => { if (status !== 'error') status = 'paused'; }} onerror={() => status = 'error'}></audio>
    </section>

    <section class="container short-links" aria-label="ลิงก์สำคัญ">
      <a href="#listen" class="short-link"><span class="tile-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M12 3v18M8 7a7 7 0 0 0 0 10M16 7a7 7 0 0 1 0 10"/><path d="M4 3a13 13 0 0 0 0 18M20 3a13 13 0 0 1 0 18"/></svg></span><strong>ฟังวิทยุสด</strong><small>เปิดฟังสถานี RCAT</small></a>
      <a href="#about" class="short-link"><span class="tile-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 9h8M8 13h8M8 17h5"/></svg></span><strong>เกี่ยวกับสถานี</strong><small>รู้จัก RCAT Radio</small></a>
      <a href={COLLEGE_URL} target="_blank" rel="noopener noreferrer" class="short-link"><span class="tile-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10.5 12 4l9 6.5V20H3v-9.5Z"/><path d="M9 20v-7h6v7"/></svg></span><strong>เว็บไซต์วิทยาลัย</strong><small>ข้อมูลและประชาสัมพันธ์ ↗</small></a>
    </section>

    <section id="about" class="container about-section" aria-labelledby="about-heading">
      <div class="about-emblem" aria-hidden="true"><span>RCAT</span><svg viewBox="0 0 60 45" width="65" height="50"><path d="M9 35c9-2 12-9 20-14 9-6 17-8 24-10-2 21-10 30-27 29" fill="#c9e779"/><path d="M14 43C24 30 36 21 53 11" fill="none" stroke="#106937" stroke-width="2"/></svg></div>
      <div><span class="section-kicker">ABOUT THE STATION</span><h2 id="about-heading">สถานีวิทยุออนไลน์ RCAT</h2><p>พื้นที่เสียงเพื่อการเรียนรู้และการสื่อสารของวิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด เชื่อมโยงสาระด้านการศึกษา เกษตร และนวัตกรรมสู่ชุมชน</p></div>
    </section>
  </main>

  <footer class="footer"><div class="container footer-inner"><div><strong>RCAT Radio Network</strong><span>เสียงเพื่อการเรียนรู้ เกษตร นวัตกรรม และชุมชน</span></div><a href="#listen">ฟังวิทยุออนไลน์ <span aria-hidden="true">↗</span></a></div></footer>
</div>
