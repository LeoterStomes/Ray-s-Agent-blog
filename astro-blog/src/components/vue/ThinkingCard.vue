<template>
  <div class="thinking-card" :class="{ collapsed: collapsed }">
    <button class="thinking-header" @click="collapsed = !collapsed">
      <span class="thinking-icon">&#x1F4AD;</span>
      <span class="thinking-label">{{ collapsed ? '思考过程' : '思考过程' }}</span>
      <svg class="thinking-chevron" :class="{ open: !collapsed }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>
    <div v-show="!collapsed" class="thinking-content">
      <p>{{ text }}</p>
      <span v-if="streaming" class="cursor-blink">|</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{ text: string; streaming?: boolean }>();
const collapsed = ref(true);
</script>

<style scoped>
.thinking-card {
  margin: 4px 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}
.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 10px;
  background: #f9fafb;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  font-size: 12px;
}
.thinking-header:hover { background: #f3f4f6; }
.thinking-icon { font-size: 14px; }
.thinking-label { flex: 1; text-align: left; }
.thinking-chevron { transition: transform 0.2s; }
.thinking-chevron.open { transform: rotate(180deg); }
.thinking-content {
  padding: 8px 12px;
  color: #6b7280;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor-blink {
  animation: blink 1s step-end infinite;
  color: #5b7bff;
}
@keyframes blink {
  50% { opacity: 0; }
}
</style>
