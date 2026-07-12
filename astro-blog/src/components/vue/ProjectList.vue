<template>
  <div>
    <!-- Search -->
    <div class="mb-8">
      <input v-model="search" @input="load" placeholder="搜索项目..." class="w-full max-w-md px-4 py-2.5 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500 glass-card" />
    </div>

    <!-- Grid -->
    <div v-if="items.length === 0" class="text-center py-20 text-gray-400">暂无项目</div>
    <div v-else class="grid grid-cols-3 gap-5 max-lg:grid-cols-2 max-sm:grid-cols-1">
      <div v-for="p in items" :key="p.id" class="glass-card p-5 hover:shadow-card-hover transition-all group">
        <div class="flex items-start justify-between mb-3">
          <h2 class="text-lg font-bold text-gray-800 truncate flex-1">{{ p.name }}</h2>
          <a v-if="p.github_url" :href="p.github_url" target="_blank" class="text-gray-400 hover:text-gray-700 transition-colors ml-2 flex-shrink-0" title="GitHub">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          </a>
        </div>
        <p class="text-sm text-gray-500 leading-relaxed mb-3 line-clamp-3">{{ p.description || '暂无介绍' }}</p>
        <div class="flex flex-wrap gap-1.5">
          <span v-for="tag in (p.tags || '').split(',').filter(Boolean)" :key="tag" class="text-[11px] px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 font-medium">{{ tag.trim() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const items = ref<any[]>([]);
const search = ref('');

onMounted(load);

async function load() {
  const params = search.value ? `?keyword=${encodeURIComponent(search.value)}` : '';
  try {
    const r = await fetch(`/api/project/list${params}`);
    const j = await r.json();
    if (j.code === '200') items.value = j.data;
  } catch { /* ignore */ }
}
</script>