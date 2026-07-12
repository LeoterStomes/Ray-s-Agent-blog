<template>
  <div class="glass-card p-4 text-center">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center justify-center gap-1.5">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
      站点
    </h3>

    <div class="space-y-3">
      <!-- 实时在线 -->
      <div>
        <div class="flex items-center justify-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <div class="text-2xl font-bold text-green-500 tabular-nums">{{ online }}</div>
        </div>
        <div class="text-xs text-gray-400">在线访客</div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <div class="text-lg font-semibold text-gray-600">{{ stats.articles }}</div>
          <div class="text-xs text-gray-400">文章</div>
        </div>
        <div>
          <div class="text-lg font-semibold text-gray-600">{{ stats.categories }}</div>
          <div class="text-xs text-gray-400">分类</div>
        </div>
        <div>
          <div class="text-lg font-semibold text-gray-600">{{ totalVisits }}</div>
          <div class="text-xs text-gray-400">总访问</div>
        </div>
        <div>
          <div class="text-lg font-semibold text-gray-600">{{ stats.views }}</div>
          <div class="text-xs text-gray-400">阅读</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

defineProps<{ stats: { articles: number; categories: number; views: number } }>();

const online = ref(1);
const totalVisits = ref(0);
let timer: ReturnType<typeof setInterval>;
const INTERVAL = 6 * 60 * 60 * 1000; // 6 hours

async function fetchStats() {
  try {
    const res = await fetch('/api/visitor/stats');
    const json = await res.json();
    if (json.code === '200') {
      online.value = json.data.online;
      totalVisits.value = json.data.total;
    }
  } catch { /* ignore */ }
}

async function ping() {
  try { await fetch('/api/visitor/ping', { method: 'POST' }); } catch { /* ignore */ }
}

onMounted(() => {
  ping();
  fetchStats();
  timer = setInterval(fetchStats, INTERVAL);
});

onUnmounted(() => clearInterval(timer));
</script>
