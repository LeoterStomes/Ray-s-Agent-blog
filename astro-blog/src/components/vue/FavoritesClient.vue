<template>
  <div>
    <!-- Not logged in -->
    <div v-if="!loggedIn" class="text-center py-16 glass-card">
      <p class="text-gray-400 text-lg mb-4">请先登录查看收藏</p>
      <button @click="$openAuth('login')" class="px-6 py-2.5 rounded-button bg-brand-600 text-white font-medium hover:bg-brand-700 transition-colors">
        去登录
      </button>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="text-center py-16 glass-card">
      <p class="text-gray-400">加载中...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="items.length === 0" class="text-center py-16 glass-card">
      <p class="text-gray-400 text-lg mb-2">暂无收藏</p>
      <a href="/blog" class="text-brand-600 hover:text-brand-700 text-sm">去发现精彩文章</a>
    </div>

    <!-- List -->
    <div v-else class="space-y-4">
      <a
        v-for="item in items"
        :key="item.id"
        :href="`/blog/${item.slug}`"
        class="glass-card p-5 flex items-center gap-4 no-underline hover:shadow-card-hover transition-all group"
      >
        <div class="flex-1 min-w-0">
          <span v-if="item.categoryName" class="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-600">
            {{ item.categoryName }}
          </span>
          <h3 class="text-base font-semibold text-gray-700 mt-2 group-hover:text-brand-600 transition-colors line-clamp-1">
            {{ item.title }}
          </h3>
          <p class="text-sm text-gray-400 mt-1 line-clamp-1">{{ item.summary }}</p>
        </div>
        <svg class="w-5 h-5 text-gray-300 group-hover:text-brand-500 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { $isLoggedIn, openAuth } from '@lib/store';
import { request } from '@lib/api';
import { API } from '@lib/constants';

interface FavItem {
  id: string;
  slug: string;
  title: string;
  summary: string;
  categoryName: string;
}

const loggedIn = ref(false);
const loading = ref(true);
const items = ref<FavItem[]>([]);

onMounted(async () => {
  loggedIn.value = $isLoggedIn.get();
  if (loggedIn.value) {
    try {
      const data = await request<any>(`${API.ENDPOINTS.FAVORITES}?currentPage=1&size=50`);
      items.value = (data.records || []).map((r: any) => ({
        id: r.id,
        slug: r.slug || r.id,
        title: r.title,
        summary: r.summary,
        categoryName: r.categoryName,
      }));
    } catch { /* ignore */ }
  }
  loading.value = false;
});
</script>
