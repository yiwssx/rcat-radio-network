<script lang="ts">
  import { onMount } from 'svelte';
  import { parsePublicSchedule, scheduleDays, showDate, showTime } from '$lib/public-schedule.js';

  let { onClose }: { onClose: () => void } = $props();
  let dialog: HTMLDialogElement;
  let state = $state<'loading' | 'ready' | 'error'>('loading');
  let mode = $state<'day' | 'week'>('day');
  const days = scheduleDays();
  let selectedDate = $state(days[0].date);
  let shows = $state<{ title: string; starts_at: string; ends_at: string }[]>([]);

  const selectedShows = $derived(shows.filter(show => showDate(show) === selectedDate));

  onMount(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    dialog.showModal();
    void (async () => {
      try {
        const response = await fetch('/radio-schedule.json', {
          headers: { Accept: 'application/json' },
          credentials: 'omit',
          cache: 'no-store',
          signal: controller.signal
        });
        if (!response.ok || !response.headers.get('content-type')?.toLowerCase().includes('application/json')) {
          throw new Error('Schedule response unavailable');
        }
        const parsed = parsePublicSchedule(await response.json());
        if (!parsed) throw new Error('Schedule stale or invalid');
        if (!controller.signal.aborted) {
          shows = parsed.shows;
          state = 'ready';
        }
      } catch {
        if (!controller.signal.aborted) state = 'error';
      } finally {
        window.clearTimeout(timeout);
      }
    })();
    return () => {
      controller.abort();
      window.clearTimeout(timeout);
      if (dialog.open) dialog.close();
    };
  });

  function closeDialog() { dialog.close(); }
</script>

<dialog bind:this={dialog} class="rrn-schedule-dialog" aria-labelledby="rrn-schedule-heading" onclose={onClose}>
  <div class="schedule-shell">
    <header class="schedule-heading">
      <div>
        <p class="schedule-eyebrow">RCAT RADIO NETWORK · PROGRAMS</p>
        <h2 id="rrn-schedule-heading">ตารางรายการออกอากาศ</h2>
        <p>ผังรายการจริงจาก LibreTime · เวลาไทย (Asia/Bangkok)</p>
      </div>
      <button class="schedule-close" type="button" aria-label="ปิดตารางรายการ" onclick={closeDialog}>×</button>
    </header>

    <div class="schedule-mode" role="group" aria-label="รูปแบบการแสดงผังรายการ">
      <button type="button" class:active={mode === 'day'} aria-pressed={mode === 'day'} onclick={() => mode = 'day'}>รายวัน</button>
      <button type="button" class:active={mode === 'week'} aria-pressed={mode === 'week'} onclick={() => mode = 'week'}>7 วันข้างหน้า</button>
    </div>

    {#if mode === 'day'}
      <div class="schedule-days" role="group" aria-label="เลือกวันออกอากาศ">
        {#each days as day (day.date)}
          <button type="button" class:selected={selectedDate === day.date} aria-pressed={selectedDate === day.date} onclick={() => selectedDate = day.date}>
            {day.today ? 'วันนี้' : day.label}
          </button>
        {/each}
      </div>
    {/if}

    <div class="schedule-content" role="status" aria-live="polite">
      {#if state === 'loading'}
        <p class="schedule-empty">กำลังโหลดผังรายการจากสถานี…</p>
      {:else if state === 'error'}
        <p class="schedule-empty">ยังไม่สามารถแสดงผังรายการได้ในขณะนี้</p>
      {:else if mode === 'day'}
        {#if selectedShows.length === 0}
          <p class="schedule-empty">ยังไม่มีรายการกำหนดไว้สำหรับวันนี้ที่เลือก</p>
        {:else}
          <ul class="schedule-list">
            {#each selectedShows as show (show.starts_at + show.title)}
              <li>
                <span class="show-time">{showTime(show.starts_at)}–{showTime(show.ends_at)}</span>
                <strong>{show.title}</strong>
              </li>
            {/each}
          </ul>
        {/if}
      {:else}
        <div class="schedule-week">
          {#each days as day (day.date)}
            {@const dayShows = shows.filter(show => showDate(show) === day.date)}
            <section class="schedule-day-group" aria-label={day.today ? 'วันนี้' : day.label}>
              <h3>{day.today ? 'วันนี้' : day.label}</h3>
              {#if dayShows.length}
                <ul class="schedule-list">
                  {#each dayShows as show (show.starts_at + show.title)}
                    <li>
                      <span class="show-time">{showTime(show.starts_at)}–{showTime(show.ends_at)}</span>
                      <strong>{show.title}</strong>
                    </li>
                  {/each}
                </ul>
              {:else}
                <p class="schedule-no-show">ยังไม่มีรายการในผัง</p>
              {/if}
            </section>
          {/each}
        </div>
      {/if}
    </div>
    <p class="schedule-footnote">แสดงเฉพาะรายการที่จัดไว้ใน LibreTime ไม่รวมเพลงที่เปิดนอกผังรายการ</p>
  </div>
</dialog>

<style>
  .rrn-schedule-dialog { width:min(92vw,780px); max-height:min(90dvh,900px); margin:auto; padding:0; border:1px solid #d8e5dc; border-radius:20px; background:#fff; color:#182a20; box-shadow:0 22px 80px #0d291a38; }
  .rrn-schedule-dialog::backdrop { background:rgba(3,21,12,.62); backdrop-filter:blur(2px); }
  .schedule-shell { padding:clamp(16px,3vw,30px); }
  .schedule-heading { display:flex; justify-content:space-between; align-items:start; gap:12px; }
  .schedule-heading h2 { font-size:clamp(19px,3vw,27px); font-weight:850; margin:4px 0 6px; }
  .schedule-heading p { margin:0; font-size:12px; color:#557060; }
  .schedule-heading .schedule-eyebrow { color:#157c43; font-size:10px; font-weight:850; letter-spacing:.12em; }
  .schedule-close { flex:none; width:37px; height:37px; font-size:29px; line-height:1; border-radius:11px; border:1px solid #d8e5dc; background:#fff; color:#29553a; cursor:pointer; }
  .schedule-close:hover { background:#f0f8f2; }
  .schedule-mode { display:flex; gap:6px; background:#f0f6f2; padding:5px; border-radius:12px; margin:20px 0 12px; }
  .schedule-mode button { flex:1; border:0; border-radius:9px; cursor:pointer; background:transparent; padding:10px; font-weight:750; color:#486151; }
  .schedule-mode button.active { background:#fff; color:#116636; box-shadow:0 1px 4px #133b1f1d; }
  .schedule-days { display:flex; gap:7px; overflow-x:auto; padding:4px 1px 13px; scrollbar-width:thin; }
  .schedule-days button { flex:none; border:1px solid #d7e4db; border-radius:10px; background:#fff; color:#345642; padding:9px 11px; cursor:pointer; font-size:12px; font-weight:700; }
  .schedule-days button.selected { border-color:#238351; color:#fff; background:#187945; }
  .schedule-content { max-height:50dvh; overflow-y:auto; min-height:90px; }
  .schedule-list { list-style:none; display:grid; gap:8px; padding:0; margin:0; }
  .schedule-list li { display:grid; grid-template-columns:122px minmax(0,1fr); align-items:center; gap:14px; border:1px solid #e4eee7; background:#fbfdfb; padding:14px 16px; border-radius:12px; }
  .schedule-list strong { font-size:14px; line-height:1.5; overflow-wrap:anywhere; }
  .show-time { font-size:12px; color:#147a44; font-weight:800; font-variant-numeric:tabular-nums; }
  .schedule-empty { text-align:center; color:#65776a; border:1px dashed #d7e2da; background:#f8fbf8; border-radius:12px; padding:25px 12px; font-size:13px; }
  .schedule-week { display:grid; gap:18px; }
  .schedule-day-group h3 { margin:0 0 9px; font-size:14px; color:#204d31; }
  .schedule-no-show { font-size:12px; margin:0; color:#708177; padding:8px 2px 12px; }
  .schedule-footnote { color:#758478; font-size:11px; line-height:1.6; margin:14px 0 0; }
  button:focus-visible { outline:3px solid #3da36c; outline-offset:3px; }
  @media(max-width:600px) {
    .rrn-schedule-dialog { width:calc(100vw - 20px); max-height:92dvh; border-radius:17px; }
    .schedule-shell { padding:17px; }
    .schedule-list li { grid-template-columns:1fr; gap:4px; padding:12px; }
    .schedule-content { max-height:52dvh; }
  }
</style>
