<template>
  <!-- Floating search trigger -->
  <button
    @click="open"
    class="fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full bg-brand-600 text-white shadow-lg hover:bg-brand-700 hover:shadow-xl transition-all flex items-center justify-center"
    title="搜索文章 (Ctrl+K)"
  >
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  </button>

  <!-- Search Overlay -->
  <Teleport to="body">
    <Transition name="overlay">
      <div v-if="visible" class="fixed inset-0 z-[110] flex items-start justify-center pt-[15vh] p-4" @click.self="close">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" />
        <div class="relative w-full max-w-lg glass-card p-4 shadow-2xl">
          <div class="flex items-center gap-3 pb-3 border-b border-gray-100">
            <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref="inputRef"
              v-model="keyword"
              @input="search"
              @keydown.esc="close"
              type="text"
              placeholder="搜索文章..."
              class="flex-1 outline-none text-gray-700 placeholder-gray-400 bg-transparent"
            />
            <kbd class="hidden sm:inline text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">ESC</kbd>
          </div>

          <!-- Results -->
          <div class="mt-2 max-h-64 overflow-y-auto">
            <div v-if="loading" class="py-8 text-center text-sm text-gray-400">
              搜索中...
            </div>
            <div v-else-if="results.length === 0 && keyword" class="py-8 text-center text-sm text-gray-400">
              未找到相关文章
            </div>
            <a
              v-for="item in results"
              :key="item.id"
              :href="`/blog/${item.slug}`"
              @click="close"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 transition-colors group"
            >
              <span v-if="item.categoryName" class="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 flex-shrink-0">
                {{ item.categoryName }}
              </span>
              <span class="text-sm text-gray-700 group-hover:text-brand-600 transition-colors truncate">
                {{ item.title }}
              </span>
            </a>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { request } from '@lib/api';
import { API } from '@lib/constants';

interface SearchResult {
  id: string;
  slug: string;
  title: string;
  categoryName: string;
}

const visible = ref(false);
const keyword = ref('');
const results = ref<SearchResult[]>([]);
const loading = ref(false);
const inputRef = ref<HTMLInputElement>();
let debounceTimer: ReturnType<typeof setTimeout>;

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    open();
  }
  if (e.key === 'Escape' && visible.value) {
    close();
  }
}

function open() {
  visible.value = true;
  setTimeout(() => inputRef.value?.focus(), 50);
}

function close() {
  visible.value = false;
  keyword.value = '';
  results.value = [];
}

function search() {
  clearTimeout(debounceTimer);
  if (!keyword.value.trim()) {
    results.value = [];
    return;
  }
  loading.value = true;
  debounceTimer = setTimeout(async () => {
    try {
      const data = await request<any>(`${API.ENDPOINTS.ARTICLES}?keyword=${encodeURIComponent(keyword.value)}&size=5`);
      results.value = (data.records || []).map((r: any) => ({
        id: r.id,
        slug: r.slug || r.id,
        title: r.title,
        categoryName: r.categoryName,
      }));
    } catch {
      results.value = [];
    } finally {
      loading.value = false;
    }
  }, 300);
}
</script>

<style scoped>
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.2s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
