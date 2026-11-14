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
  <div class="song-grid">
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
  <p class="song-footnote">ข้อมูลแสดงตามผัง LibreTime และอาจเปลี่ยนแปลงระหว่างการจัดรายการสด</p>
</section>
