<template>
  <div class="glass-card p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/></svg>
      公告
    </h3>
    <div v-if="items.length === 0" class="text-xs text-gray-400 text-center py-2">暂无公告</div>
    <div v-else class="space-y-1.5">
      <a
        v-for="(item, i) in items"
        :key="item.id"
        :href="item.link || undefined"
        :class="[
          'block text-xs rounded-lg p-2.5 leading-relaxed transition-colors',
          i === 0 ? 'bg-amber-50 border border-amber-100 text-gray-700' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
        ]"
        :style="{ textDecoration: item.link ? 'none' : 'none' }"
      >
        <span v-if="i === 0" class="text-amber-600 font-medium mr-1 text-[11px]">New</span>
        {{ item.content }}
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Announcement {
  id: number;
  content: string;
  link: string;
}

const items = ref<Announcement[]>([]);

onMounted(async () => {
  try {
    const res = await fetch('/api/announcement/list');
    const json = await res.json();
    if (json.code === '200') items.value = json.data;
  } catch { /* ignore */ }
});
</script>