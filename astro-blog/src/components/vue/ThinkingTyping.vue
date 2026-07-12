<template>
  <span class="thinking-wrap">
    <span class="thinking-dots" />
    <span class="thinking-label">{{ currentLabel }}</span>
  </span>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const labels = [
  '正在思考...',
  '查阅资料中...',
  '马上就好...',
  '整理信息中...',
  '分析问题中...',
  '调用工具中...',
  '正在检索...',
  '即将完成...',
  '稍等片刻...',
  '处理中...',
];
const currentLabel = ref(labels[0]);
let timer: ReturnType<typeof setInterval> | null = null;
let idx = 0;

onMounted(() => {
  timer = setInterval(() => {
    idx = (idx + 1) % labels.length;
    currentLabel.value = labels[idx];
  }, 2000);
});

onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
.thinking-wrap {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; color: #94a3b8; font-style: italic;
  padding: 6px 10px;
}
.thinking-dots {
  color: #5b7bff; font-size: 14px; letter-spacing: 2px;
}
.thinking-dots::after {
  content: '';
  animation: dotCycle 1.5s steps(1, end) infinite;
}
@keyframes dotCycle {
  0%, 10%  { content: '·'; }
  20%, 30% { content: '··'; }
  40%, 50% { content: '···'; }
  60%, 70% { content: '····'; }
  80%, 90% { content: ''; }
}
.thinking-label {
  transition: opacity 0.3s;
}
</style>
