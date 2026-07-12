<template>
  <div class="glass-card p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>
      音乐
    </h3>

    <div v-if="playlist.length === 0" class="text-xs text-gray-400 text-center py-4">暂无音乐</div>

    <div v-if="playlist.length > 0">
      <div class="text-center mb-3">
        <p class="text-xs font-semibold text-gray-700 truncate">{{ current.title }}</p>
        <p class="text-[10px] text-gray-400 truncate">{{ current.artist }}</p>
      </div>

      <div class="relative w-full h-1 bg-gray-200 rounded-full mb-2 cursor-pointer" @click="seek">
        <div class="absolute left-0 top-0 h-full bg-brand-600 rounded-full transition-all duration-300" :style="{ width: progress + '%' }" />
      </div>
      <div class="flex justify-between text-[10px] text-gray-400 mb-3">
        <span>{{ formatTime(currentTime) }}</span><span>{{ formatTime(duration) }}</span>
      </div>

      <div class="flex items-center justify-center gap-4">
        <button @click="prev" class="text-gray-500 hover:text-gray-700" :disabled="playlist.length <= 1">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
        </button>
        <button @click="togglePlay" class="w-9 h-9 rounded-full bg-brand-600 text-white flex items-center justify-center hover:bg-brand-700 shadow-sm">
          <svg v-if="!playing" class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <button @click="next" class="text-gray-500 hover:text-gray-700" :disabled="playlist.length <= 1">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
        </button>
      </div>

      <div class="flex items-center gap-2 mt-3 px-1">
        <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072M6.5 8.5H3a1 1 0 00-1 1v5a1 1 0 001 1h3.5l5 4.5V4l-5 4.5z"/></svg>
        <input v-model.number="volume" type="range" min="0" max="1" step="0.05" class="w-full h-1 accent-brand-600 cursor-pointer" @input="setVolume" />
      </div>

      <button @click="showList = !showList" class="w-full mt-3 text-[11px] text-gray-400 hover:text-gray-600 flex items-center justify-center gap-1">
        <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-90': showList }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        {{ showList ? '收起' : '播放列表' }} ({{ playlist.length }})
      </button>

      <div v-if="showList" class="mt-2 space-y-0.5 max-h-[180px] overflow-y-auto">
        <div v-for="(s, i) in playlist" :key="s.id" @click="selectTrack(i)"
          :class="['flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer', i === index ? 'bg-brand-50 text-brand-600 font-medium' : 'text-gray-600 hover:bg-gray-50']">
          <span class="truncate flex-1">{{ s.title }}</span>
          <span class="text-[10px] text-gray-400 ml-1">{{ s.artist }}</span>
        </div>
      </div>

      <div v-if="currentLine" class="mt-3 text-center animate-fade-in">
        <p class="text-[11px] text-gray-500 italic leading-relaxed">{{ currentLine }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

interface Track { id: number; title: string; artist: string; url: string; lyrics?: string }

const playlist = ref<Track[]>([]);
const index = ref(0);
const playing = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const lyricLines = ref<{ time: number; text: string }[]>([]);
const currentLine = ref('');
const volume = ref(0.7);
const showList = ref(false);
let tickTimer: ReturnType<typeof setInterval> | null = null;
let audio: HTMLAudioElement | null = null;

const current = computed(() => playlist.value[index.value] || { title: '', artist: '', url: '' });
const progress = computed(() => duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0);

function formatTime(s: number) { const m = Math.floor(s / 60), sec = Math.floor(s % 60); return `${m}:${String(sec).padStart(2, '0')}`; }

function parseLRC(lrc: string) {
  const lines: { time: number; text: string }[] = [];
  const regex = /\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\]/g;
  for (const raw of lrc.split('\n')) {
    const matches = [...raw.matchAll(regex)];
    const text = raw.replace(regex, '').trim();
    for (const m of matches) {
      lines.push({ time: parseInt(m[1]) * 60 + parseInt(m[2]) + (m[3] ? parseInt(m[3].padEnd(3, '0')) / 1000 : 0), text });
    }
    if (matches.length === 0 && raw.trim()) lines.push({ time: 9999, text: raw.trim() });
  }
  return lines.sort((a, b) => a.time - b.time);
}

onMounted(async () => {
  try {
    const res = await fetch('/api/music/list');
    const json = await res.json();
    if (json.code === '200') playlist.value = json.data;
  } catch { /* */ }

  // Restore state from global
  volume.value = 0.7;
  const ga = (window as any).__m?.getAudio?.();
  if (ga) {
    playing.value = !ga.paused;
    currentTime.value = ga.currentTime || 0;
    duration.value = ga.duration || 0;
    // Find current track by URL
    const idx = playlist.value.findIndex((t: Track) => ga.src.includes(t.url));
    if (idx >= 0) index.value = idx;
  }

  // Tick for progress update
  tickTimer = setInterval(() => {
    const a = (window as any).__m?.getAudio?.();
    if (a) {
      currentTime.value = a.currentTime || 0;
      duration.value = a.duration || 0;
      playing.value = !a.paused;
    }
  }, 500);
});

onUnmounted(() => { if (tickTimer) clearInterval(tickTimer); });

function togglePlay() {
  const isPlaying = (window as any).__m.isPlaying?.();
  if (isPlaying) {
    (window as any).__m.pause?.();
    playing.value = false;
  } else {
    (window as any).__m.play?.(current.value.url, volume.value, currentTime.value);
    playing.value = true;
  }
}
function prev() { index.value = (index.value - 1 + playlist.value.length) % playlist.value.length; loadTrack(); }
function next() { index.value = (index.value + 1) % playlist.value.length; loadTrack(); }
function loadTrack() {
  lyricLines.value = current.value.lyrics ? parseLRC(current.value.lyrics) : [];
  currentLine.value = ''; currentTime.value = 0; duration.value = 0;
  if (playing.value) {
    (window as any).__m.play?.(current.value.url, volume.value, 0);
  }
}
function seek(e: MouseEvent) {
  const a = (window as any).__m.getAudio?.();
  if (!a) return;
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
  a.currentTime = ((e.clientX - rect.left) / rect.width) * (a.duration || 0);
}
function setVolume() { (window as any).__m.setVol?.(volume.value); }
function selectTrack(i: number) { index.value = i; loadTrack(); playing.value = true; togglePlay(); showList.value = false; }
</script>

<style scoped>
@keyframes fade-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-in { animation: fade-in 0.4s ease; }
</style>