<template>
  <div v-if="visible" class="tool-thinking">
    <span v-if="!timedOut" class="spinner" />
    <span v-else class="check">&#10003;</span>
    <span class="thinking-text">{{ timedOut ? displayName : 'thinking...' }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { TOOL_NAMES } from '@lib/toolNames';

const props = defineProps<{
  tool: string;
  args?: Record<string, any>;
  status?: 'running' | 'done' | 'error';
}>();

const displayName = computed(() => TOOL_NAMES[props.tool] || props.tool);
const timedOut = ref(false);
const visible = ref(true);
let timer: ReturnType<typeof setTimeout> | null = null;

onMounted(() => {
  if (props.status === 'running') {
    // 5秒后自动标记完成
    timer = setTimeout(() => { timedOut.value = true; }, 5000);
    // 8秒后自动隐藏
    setTimeout(() => { visible.value = false; }, 8000);
  } else {
    timedOut.value = true;
  }
});

onUnmounted(() => { if (timer) clearTimeout(timer); });
</script>

<style scoped>
.tool-thinking {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; color: #94a3b8; font-size: 12px;
}
.spinner {
  width: 14px; height: 14px;
  border: 2px solid #e2e8f0;
  border-top-color: #94a3b8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.thinking-text { font-style: italic; }
.check { font-size: 12px; color: #16a34a; }
</style>
