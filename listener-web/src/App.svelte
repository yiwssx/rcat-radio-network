<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Card } from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import TrackTimeline from "$lib/TrackTimeline.svelte";
  type PlaybackStatus = 'idle' | 'connecting' | 'playing' | 'paused' | 'error';
  const STREAM_URL = 'https://radio.rcat.ac.th:8600/main.mp3';
  const COLLEGE_URL = 'https://www.rcat.ac.th/';
  // All public destinations below are published on https://www.rcat.ac.th/.
  const NEWS_URL = 'https://www.rcat.ac.th/news';
  const CONTACT_URL = 'https://www.rcat.ac.th/contact';
  const SOCIAL_URLS = {
    facebook: 'https://www.facebook.com/profile.php?id=100063746585360',
    youtube: 'https://www.youtube.com/@RCAT101',
    tiktok: 'https://www.tiktok.com/@rcat_101',
    website: COLLEGE_URL
  } as const;

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
        <!-- Original college emblem supplied by the owner, stored without modification at public/images/RCAT.png. -->
        <img class="college-mark" src="/images/RCAT.png" alt="" width="68" height="68" decoding="async" />
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
      <nav class:opened={menuOpen} class="navlinks" id="primary-nav" aria-label="เมนูหลัก">
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
        <a href={NEWS_URL} target="_blank" rel="noopener noreferrer" onclick={() => menuOpen = false}>ข่าวสาร</a>
        <a href="#about" onclick={() => menuOpen = false}>เกี่ยวกับสถานี</a>
      </nav>
      <Button variant="ghost" class="menu-toggle" aria-label={menuOpen ? 'ปิดเมนู' : 'เปิดเมนู'} aria-expanded={menuOpen} aria-controls="primary-nav" onclick={() => menuOpen = !menuOpen}>
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
      </Button>
    </div>
  </header>

  <main>
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-photo" aria-hidden="true">
        <!-- The supplied AI-enhanced campus photo has unreadable generated glyphs
             on this plaque. Render the exact operator-supplied wording as DOM text
             over the plaque; keep the photographed building and original asset intact. -->
        <div class="hero-photo-canvas">
          <div class="hero-plaque-text">
            <span>การประชุมวิชาการระดับชาติองค์การเกษตรกรในอนาคตแห่งประเทศไทย</span>
            <span>ในพระราชูปถัมภ์สมเด็จพระเทพรัตนราชสุดาฯ สยามบรมราชกุมารี</span>
            <span>ครั้งที่ ๒๗ ๒๐-๒๓ กุมภาพันธ์ ๒๕๔๘</span>
            <span>ณ วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</span>
          </div>
        </div>
      </div>
      <div class="hero-shade" aria-hidden="true"></div>
      <p class="sr-only">ภาพวิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด พร้อมข้อความ เรียนฟรี หอพักฟรี อาหารฟรี มีรายได้ระหว่างเรียน และป้ายการประชุมวิชาการระดับชาติองค์การเกษตรกรในอนาคตแห่งประเทศไทย ในพระราชูปถัมภ์สมเด็จพระเทพรัตนราชสุดาฯ สยามบรมราชกุมารี ครั้งที่ ๒๗ ๒๐-๒๓ กุมภาพันธ์ ๒๕๔๘ ณ วิทยาลัยเกษตรและเทคโนโลยีร้อยเอ็ด</p>
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
      <Card class="player-panel">
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
          <Badge variant="secondary" class="radio-chip"><svg class="chip-broadcast" aria-hidden="true" focusable="false"
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
 สด</Badge>
          <p class="playing-label">สตรีมวิทยุออนไลน์</p>
          <h2>RCAT Radio Network</h2>
        </div>
        <div class="player-play-area">
          <Button variant="default" size="icon-lg" class="play-button" onclick={togglePlayback} aria-label={isPlaying || isConnecting ? 'หยุดฟังวิทยุ' : 'เริ่มฟังวิทยุ'} title={isPlaying || isConnecting ? 'หยุดฟัง' : 'ฟังวิทยุสด'}>
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
          </Button>
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
      </Card>
      <audio bind:this={audioElement} src={STREAM_URL} preload="none"
        onplaying={() => status = 'playing'}
        onwaiting={() => { if (status !== 'paused') status = 'connecting'; }}
        onpause={() => { if (status !== 'error') status = 'paused'; }}
        onended={() => status = 'error'}
        onerror={() => status = 'error'}></audio>

    </section>

    <section class="short-links" aria-label="ลิงก์สำคัญ">
      <div class="shortcut-grid">
        <Button variant="outline" class="short-link" onclick={openSchedule} title="ตารางรายการ — เร็ว ๆ นี้">
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

          <strong>ตารางรายการ</strong><Badge variant="outline" class="short-link-status">เร็ว ๆ นี้</Badge>
        </Button>
        <Button variant="outline" class="short-link" href={NEWS_URL} target="_blank" rel="noopener noreferrer">
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
        </Button>
        <Button variant="outline" class="short-link" onclick={openActivity} title="กิจกรรมสถานี — เร็ว ๆ นี้">
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

          <strong>กิจกรรมสถานี</strong><Badge variant="outline" class="short-link-status">เร็ว ๆ นี้</Badge>
        </Button>
        <Button variant="outline" class="short-link" href={CONTACT_URL} target="_blank" rel="noopener noreferrer">
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
        </Button>
        {#if scheduleNotice || activityNotice}<div class="schedule-notice" role="status">{scheduleNotice ? 'ยังไม่มีตารางรายการเผยแพร่ในขณะนี้' : 'ยังไม่มีข้อมูลกิจกรรมสถานีเผยแพร่ในขณะนี้'} <button onclick={() => {scheduleNotice = false; activityNotice = false;}}>ปิด</button></div>{/if}
      </div>
      <div class="follow-section"><h2>ติดตามเราได้ที่</h2><div class="socials">
        <a class="facebook" aria-label="Facebook วิทยาลัย" target="_blank" rel="noopener noreferrer" href={SOCIAL_URLS.facebook} title="Facebook"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="social-brand-icon bootstrap-facebook" aria-hidden="true" focusable="false" viewBox="0 0 16 16">
  <path d="M16 8.049c0-4.446-3.582-8.05-8-8.05C3.58 0-.002 3.603-.002 8.05c0 4.017 2.926 7.347 6.75 7.951v-5.625h-2.03V8.05H6.75V6.275c0-2.017 1.195-3.131 3.022-3.131.876 0 1.791.157 1.791.157v1.98h-1.009c-.993 0-1.303.621-1.303 1.258v1.51h2.218l-.354 2.326H9.25V16c3.824-.604 6.75-3.934 6.75-7.951"/>
</svg></a>
        <a class="youtube" aria-label="YouTube วิทยาลัย" target="_blank" rel="noopener noreferrer" href={SOCIAL_URLS.youtube} title="Youtube"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="social-brand-icon bootstrap-youtube" aria-hidden="true" focusable="false" viewBox="0 0 16 16">
  <path d="M8.051 1.999h.089c.822.003 4.987.033 6.11.335a2.01 2.01 0 0 1 1.415 1.42c.101.38.172.883.22 1.402l.01.104.022.26.008.104c.065.914.073 1.77.074 1.957v.075c-.001.194-.01 1.108-.082 2.06l-.008.105-.009.104c-.05.572-.124 1.14-.235 1.558a2.01 2.01 0 0 1-1.415 1.42c-1.16.312-5.569.334-6.18.335h-.142c-.309 0-1.587-.006-2.927-.052l-.17-.006-.087-.004-.171-.007-.171-.007c-1.11-.049-2.167-.128-2.654-.26a2.01 2.01 0 0 1-1.415-1.419c-.111-.417-.185-.986-.235-1.558L.09 9.82l-.008-.104A31 31 0 0 1 0 7.68v-.123c.002-.215.01-.958.064-1.778l.007-.103.003-.052.008-.104.022-.26.01-.104c.048-.519.119-1.023.22-1.402a2.01 2.01 0 0 1 1.415-1.42c.487-.13 1.544-.21 2.654-.26l.17-.007.172-.006.086-.003.171-.007A100 100 0 0 1 7.858 2zM6.4 5.209v4.818l4.157-2.408z"/>
</svg></a>
        <a class="tiktok" aria-label="TikTok วิทยาลัย" target="_blank" rel="noopener noreferrer" href={SOCIAL_URLS.tiktok} title="Tiktok"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="social-brand-icon bootstrap-tiktok" aria-hidden="true" focusable="false" viewBox="0 0 16 16">
  <path d="M9 0h1.98c.144.715.54 1.617 1.235 2.512C12.895 3.389 13.797 4 15 4v2c-1.753 0-3.07-.814-4-1.829V11a5 5 0 1 1-5-5v2a3 3 0 1 0 3 3z"/>
</svg></a>
        <a class="website" aria-label="เว็บไซต์วิทยาลัย" target="_blank" rel="noopener noreferrer" href={SOCIAL_URLS.website}><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="social-brand-icon bootstrap-globe" aria-hidden="true" focusable="false" viewBox="0 0 16 16">
  <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m7.5-6.923c-.67.204-1.335.82-1.887 1.855A8 8 0 0 0 5.145 4H7.5zM4.09 4a9.3 9.3 0 0 1 .64-1.539 7 7 0 0 1 .597-.933A7.03 7.03 0 0 0 2.255 4zm-.582 3.5c.03-.877.138-1.718.312-2.5H1.674a7 7 0 0 0-.656 2.5zM4.847 5a12.5 12.5 0 0 0-.338 2.5H7.5V5zM8.5 5v2.5h2.99a12.5 12.5 0 0 0-.337-2.5zM4.51 8.5a12.5 12.5 0 0 0 .337 2.5H7.5V8.5zm3.99 0V11h2.653c.187-.765.306-1.608.338-2.5zM5.145 12q.208.58.468 1.068c.552 1.035 1.218 1.65 1.887 1.855V12zm.182 2.472a7 7 0 0 1-.597-.933A9.3 9.3 0 0 1 4.09 12H2.255a7 7 0 0 0 3.072 2.472M3.82 11a13.7 13.7 0 0 1-.312-2.5h-2.49c.062.89.291 1.733.656 2.5zm6.853 3.472A7 7 0 0 0 13.745 12H11.91a9.3 9.3 0 0 1-.64 1.539 7 7 0 0 1-.597.933M8.5 12v2.923c.67-.204 1.335-.82 1.887-1.855q.26-.487.468-1.068zm3.68-1h2.146c.365-.767.594-1.61.656-2.5h-2.49a13.7 13.7 0 0 1-.312 2.5m2.802-3.5a7 7 0 0 0-.656-2.5H12.18c.174.782.282 1.623.312 2.5zM11.27 2.461c.247.464.462.98.64 1.539h1.835a7 7 0 0 0-3.072-2.472c.218.284.418.598.597.933M10.855 4a8 8 0 0 0-.468-1.068C9.835 1.897 9.17 1.282 8.5 1.077V4z"/>
</svg>
</a>
      </div></div>
    </section>

    <TrackTimeline />
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