<template>
  <div class="glass-card p-4 text-center">
    <div class="text-xs text-gray-400 mb-1">{{ dateStr }}</div>
    <div class="text-4xl font-extrabold brand-text tabular-nums">{{ day }}</div>
    <div class="text-xs text-gray-500 mt-0.5">{{ weekday }}</div>
    <div class="text-lg font-mono font-bold text-gray-600 mt-2 tabular-nums">{{ time }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const day = ref('');
const weekday = ref('');
const dateStr = ref('');
const time = ref('');
let timer: ReturnType<typeof setInterval>;

function update() {
  const now = new Date();
  day.value = String(now.getDate()).padStart(2, '0');
  weekday.value = '星期' + ['日', '一', '二', '三', '四', '五', '六'][now.getDay()];
  dateStr.value = `${now.getFullYear()} / ${String(now.getMonth() + 1).padStart(2, '0')} / ${String(now.getDate()).padStart(2, '0')}`;
  time.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
}

onMounted(() => { update(); timer = setInterval(update, 1000); });
onUnmounted(() => clearInterval(timer));
</script>
