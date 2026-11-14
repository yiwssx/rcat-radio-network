<script lang="ts">
  import { onMount } from 'svelte';
  import { Card } from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';
  import { normalizeLiveInfo } from '$lib/live-info.js';

  type FeedState = 'unconfigured' | 'loading' | 'ready' | 'error';
  type Slot = 'previous' | 'current' | 'next';

  // Optional PUBLIC read-only endpoint. No token, cookies or private LibreTime URL.
  const configuredUrl = (import.meta.env.VITE_LIBRETIME_LIVE_INFO_URL ?? '').trim();
  const slots: { key: Slot; label: string; index: string }[] = [
    { key: 'previous', label: 'เล่นไปแล้ว', index: '01' },
    { key: 'current', label: 'กำลังเล่น', index: '02' },
    { key: 'next', label: 'เพลงถัดไป', index: '03' }
  ];
  let feedState = $state<FeedState>(configuredUrl ? 'loading' : 'unconfigured');
  let tracks = $state<ReturnType<typeof normalizeLiveInfo>>(null);
  let showMobileDetails = $state(false);

  const feedStatus = $derived(
    feedState === 'ready' ? 'ข้อมูลจากผังรายการ LibreTime' :
    feedState === 'loading' ? 'กำลังโหลดข้อมูลเพลง…' :
    feedState === 'error' ? 'ยังดึงข้อมูลเพลงไม่ได้' :
    'ยังไม่เชื่อมต่อข้อมูลเพลง'
  );

  onMount(() => {
    if (!configuredUrl) return;
    let alive = true;
    let controller: AbortController | null = null;
    let busy = false;

    const load = async () => {
      if (!alive || busy || document.hidden) return;
      busy = true;
      const request = new AbortController();
      controller = request;
      const timeout = window.setTimeout(() => request.abort(), 8000);
      try {
        const target = new URL(configuredUrl, window.location.origin);
        const localDevelopment = target.protocol === 'http:' &&
          ['localhost', '127.0.0.1'].includes(target.hostname);
        if (target.protocol !== 'https:' && !localDevelopment) {
          throw new Error('Only public HTTPS endpoints are supported');
        }
        if (target.username || target.password || [...target.searchParams.keys()].some(key => /api[_-]?key|token|secret|password|auth/i.test(key))) {
          throw new Error('Public metadata URLs must not contain credentials or API keys');
        }
        const response = await fetch(target.toString(), {
          method: 'GET',
          credentials: 'omit',
          cache: 'no-store',
          headers: { Accept: 'application/json' },
          signal: request.signal
        });
        if (!response.ok) throw new Error('Public metadata endpoint unavailable');
        const data = normalizeLiveInfo(await response.json());
        if (!data) throw new Error('Unexpected LibreTime response format');
        if (alive) {
          tracks = data;
          feedState = 'ready';
        }
      } catch {
        if (alive) {
          tracks = null; // Never claim stale track data is still on air.
          feedState = 'error';
        }
      } finally {
        window.clearTimeout(timeout);
        if (controller === request) controller = null;
        busy = false;
      }
    };

    void load();
    const timer = window.setInterval(() => void load(), 90_000);
    const refreshWhenVisible = () => { if (!document.hidden) void load(); };
    document.addEventListener('visibilitychange', refreshWhenVisible);
    return () => {
      alive = false;
      controller?.abort();
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
    };
  });
</script>

<section class="song-timeline" aria-labelledby="song-timeline-heading">
  <div class="song-heading">
    <div>
      <p class="song-eyebrow">RCAT RADIO · PLAYOUT</p>
      <h2 id="song-timeline-heading">เพลงและรายการออกอากาศ</h2>
      <p class="song-subtitle">เพลงล่าสุด ขณะนี้ และลำดับถัดไปจากระบบสถานี</p>
    </div>
    <span class:ready={feedState === 'ready'} class="song-feed-status" role="status" aria-live="polite">
      <span class="song-feed-dot" aria-hidden="true"></span>{feedStatus}
    </span>
  </div>
  <div class={showMobileDetails ? "song-grid show-all" : "song-grid"} id="song-track-grid">
    {#each slots as slot (slot.key)}
      {@const item = tracks?.[slot.key] ?? null}
      <Card class={slot.key === 'current' ? 'song-card song-card-current' : 'song-card'}>
        <div class="song-card-head">
          <span class="song-number">{slot.index}</span>
          <Badge variant={slot.key === 'current' ? 'default' : 'outline'} class="song-role">{item?.kind === 'livestream' ? 'รายการสด' : slot.label}</Badge>
        </div>
        <div class="song-information">
          {#if feedState === 'ready' && item}
            <h3 title={item.title}>{item.title}</h3>
            <p>{item.artist ?? (item.kind === 'livestream' ? 'ถ่ายทอดสดจากสถานี' : item.kind === 'webstream' ? 'รายการจากแหล่งสตรีม' : 'ข้อมูลจาก LibreTime')}</p>
          {:else}
            <h3>{feedState === 'loading' ? 'กำลังตรวจสอบรายการ…' : 'ยังไม่มีข้อมูลเพลง'}</h3>
            <p>{feedState === 'unconfigured' ? 'รอการเชื่อมต่อข้อมูลจากสถานี' : feedState === 'error' ? 'ไม่สามารถอ่านข้อมูลจากสถานีได้' : 'ยังไม่มีเพลงในผังช่วงนี้'}</p>
          {/if}
        </div>
      </Card>
    {/each}
  </div>
  <button class="song-mobile-expand" aria-controls="song-track-grid" aria-expanded={showMobileDetails} onclick={() => showMobileDetails = !showMobileDetails}>{showMobileDetails ? 'ซ่อนเพลงก่อนหน้าและถัดไป' : 'ดูเพลงก่อนหน้าและถัดไป'}</button>
  <p class="song-footnote">ข้อมูลแสดงตามผัง LibreTime และอาจเปลี่ยนแปลงระหว่างการจัดรายการสด</p>
</section>

<style>
  .song-timeline { width:min(calc(100% - 44px), 1174px); margin:4px auto 32px; }
  .song-heading { display:flex; justify-content:space-between; align-items:end; gap:16px; margin-bottom:16px; }
  .song-eyebrow { color:var(--primary); font-size:11px; font-weight:900; letter-spacing:.14em; margin:0 0 4px; }
  .song-heading h2 { font-size:clamp(20px,2.4vw,25px); letter-spacing:-.02em; margin:0; font-weight:850; }
  .song-subtitle { font-size:13px; margin:4px 0 0; color:var(--muted-foreground); }
  .song-feed-status { display:inline-flex; align-items:center; gap:7px; flex:none; color:var(--muted-foreground); font-size:12px; font-weight:650; padding:7px 11px; border:1px solid var(--border); border-radius:999px; background:#fff; }
  .song-feed-dot { width:8px; height:8px; background:#a5ada6; border-radius:50%; }
  .song-feed-status.ready .song-feed-dot { background:#29a857; }
  .song-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
  .song-grid :global(.song-card) { min-width:0; min-height:153px; padding:16px 18px; display:flex; flex-direction:column; gap:14px; background:#fff; border:1px solid var(--border); border-radius:18px; box-shadow:0 5px 16px rgba(11,70,42,.045); }
  .song-grid :global(.song-card-current) { border-color:#a7cbb4; background:linear-gradient(140deg,#f7fcf8,#edf7f0); box-shadow:0 6px 20px rgba(11,70,42,.07); }
  .song-card-head { display:flex; align-items:center; justify-content:space-between; gap:12px; }
  .song-number { font-size:11px; font-weight:900; letter-spacing:.12em; color:#80968a; }
  .song-card-head :global(.song-role) { font-size:11px; font-weight:800; }
  .song-information h3 { margin:0; font-size:17px; font-weight:800; line-height:1.34; overflow-wrap:anywhere; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  .song-information p { margin:7px 0 0; font-size:12px; line-height:1.45; color:var(--muted-foreground); overflow-wrap:anywhere; }
  .song-footnote { margin:12px 0 0; font-size:11px; color:var(--muted-foreground); }
  .song-mobile-expand { display:none; }
  @media (max-width:900px) {
    .song-timeline { width:calc(100% - 44px); }
    .song-grid { gap:10px; }
    .song-grid :global(.song-card) { padding:13px; min-height:144px; }
    .song-information h3 { font-size:15px; }
    .song-feed-status { max-width:220px; }
  }
  @media (max-width:640px) {
    .song-timeline { width:calc(100% - 32px); margin:4px auto 28px; }
    .song-heading { flex-direction:column; align-items:start; gap:10px; }
    .song-feed-status { max-width:100%; }
    .song-grid { grid-template-columns:1fr; }
    .song-grid :global(.song-card-current) { order:-1; }
    .song-grid:not(.show-all) :global(.song-card:not(.song-card-current)) { display:none; }
    .song-grid :global(.song-card) { min-height:116px; padding:14px 16px; }
    .song-mobile-expand { display:block; width:100%; margin-top:10px; border:1px solid var(--border); background:#fff; color:var(--primary); border-radius:11px; padding:11px 14px; font-size:13px; font-weight:700; cursor:pointer; }
    .song-mobile-expand:focus-visible { outline:3px solid var(--ring); outline-offset:3px; }
  }
</style>
