<template>
  <div class="glass-card p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg>
      标签
    </h3>
    <!-- 筛选输入 -->
    <input
      v-model="filter"
      type="text"
      placeholder="筛选标签..."
      class="w-full px-3 py-1.5 mb-3 text-xs border border-gray-200 rounded-lg focus:ring-1 focus:ring-brand-500 focus:border-brand-500 outline-none"
    />
    <div class="flex flex-wrap gap-2">
      <a
        v-for="tag in filteredTags"
        :key="tag.name"
        :href="`/blog?tag=${encodeURIComponent(tag.name)}`"
        class="px-2.5 py-1 rounded-full text-xs transition-all hover:scale-105"
        :class="tagSize(tag.count)"
        :style="{ backgroundColor: tagColor(tag.name), color: '#fff' }"
      >
        {{ tag.name }}{{ tag.count > 1 ? ` (${tag.count})` : '' }}
      </a>
      <p v-if="filteredTags.length === 0" class="text-xs text-gray-400">
        {{ filter ? '无匹配标签' : '暂无标签' }}
      </p>
    </div>
    <p v-if="allTags.length > 20" class="text-[10px] text-gray-400 mt-2">
      显示前 20 个标签（共 {{ allTags.length }} 个）
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface Tag { name: string; count: number }

const props = defineProps<{ tags: Tag[] }>();
const fetchedTags = ref<Tag[]>([]);
const filter = ref('');

async function fetchTags() {
  try {
    const r = await fetch('/api/knowledge/article/page?status=1&size=50');
    const j = await r.json();
    if (j.code === '200' && j.data?.records) {
      const map = new Map<string, number>();
      j.data.records.forEach((a: any) => {
        if (a.tags) {
          a.tags.split(',').filter(Boolean).forEach((t: string) => {
            const k = t.trim();
            if (k) map.set(k, (map.get(k) || 0) + 1);
          });
        }
      });
      fetchedTags.value = [...map.entries()].map(([name, count]) => ({ name, count }));
    }
  } catch {}
}

onMounted(() => {
  if (props.tags.length === 0) fetchTags();
});

const allTags = computed(() => {
  const source = props.tags.length > 0 ? props.tags : fetchedTags.value;
  return [...source].sort((a, b) => b.count - a.count);
});

const filteredTags = computed(() => {
  let result = allTags.value;
  if (filter.value.trim()) {
    const kw = filter.value.trim().toLowerCase();
    result = result.filter(t => t.name.toLowerCase().includes(kw));
  }
  return result.slice(0, 20);
});

function tagSize(count: number) {
  if (count >= 3) return 'text-xs font-semibold px-3 py-1.5';
  if (count >= 2) return 'text-xs font-medium';
  return 'text-xs';
}

const colors = ['#5b7bff', '#f59e0b', '#22c55e', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316'];
function tagColor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return colors[Math.abs(hash) % colors.length];
}
</script>
