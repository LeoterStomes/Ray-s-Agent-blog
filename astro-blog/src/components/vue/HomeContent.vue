<template>
  <div class="flex-1 min-w-0">
    <div v-if="loading" class="text-center py-20 text-gray-400">加载中...</div>
    <template v-else>
      <!-- Hero Carousel -->
      <div class="mb-8" v-if="heroArticles.length">
        <HeroCarousel :articles="heroArticles" />
      </div>

      <!-- Latest Posts -->
      <div>
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-lg font-bold text-gray-700 dark-mode-gray">最新文章</h2>
          <a href="/blog" class="text-xs text-brand-600 hover:text-brand-700 font-medium transition-colors">查看全部 →</a>
        </div>
        <div v-if="articles.length === 0" class="text-center py-16 glass-card">
          <p class="text-gray-400">暂无文章</p>
        </div>
        <div v-else class="space-y-5">
          <a v-for="a in articles" :key="a.id" :href="`/blog/${a.id}`"
            class="glass-card flex h-[180px] overflow-hidden group no-underline max-sm:flex-col max-sm:h-auto">
            <div class="w-[240px] h-full flex-shrink-0 relative overflow-hidden max-sm:w-full max-sm:h-[150px]">
              <img :src="a.coverImage || `https://picsum.photos/seed/${a.slug}/800/400`" :alt="a.title"
                class="w-full h-full object-cover transition-transform duration-400 group-hover:scale-105" loading="lazy"
                @error="(e) => { (e.target as HTMLImageElement).src = `https://picsum.photos/seed/${a.slug}2/800/400` }" />
              <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <span class="text-white text-sm font-medium">阅读全文</span>
              </div>
            </div>
            <div class="flex-1 p-4 flex flex-col justify-between min-w-0">
              <div>
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-[11px] px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 font-medium">{{ a.categoryName }}</span>
                  <span class="text-[11px] text-gray-400">约{{ Math.max(1, Math.ceil((a.summary?.length || 300) / 300)) }}分钟</span>
                </div>
                <h3 class="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 leading-relaxed group-hover:text-brand-600 transition-colors">{{ a.title }}</h3>
                <p class="text-sm text-gray-500 leading-relaxed line-clamp-2">{{ a.summary || '' }}</p>
              </div>
              <div class="flex items-center gap-3 text-xs text-gray-400 mt-3">
                <span>{{ formatDate(a.publishedAt) }}</span>
                <span>{{ a.readCount || 0 }} 阅读</span>
              </div>
            </div>
          </a>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import HeroCarousel from './HeroCarousel.vue';

const loading = ref(true);
const articles = ref<any[]>([]);
const heroArticles = ref<any[]>([]);

function formatDate(d: string) {
  if (!d) return '';
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
}

onMounted(async () => {
  try {
    const res = await fetch('/api/knowledge/article/page?status=1&size=6&currentPage=1&sortField=publishedAt&sortDirection=DESC');
    const json = await res.json();
    if (json.code === '200' && json.data?.records) {
      articles.value = json.data.records.map((r: any) => ({
        id: r.id, title: r.title, slug: r.id, summary: r.summary,
        coverImage: r.coverImage, categoryName: r.categoryName,
        readCount: r.readCount || 0, publishedAt: r.publishedAt,
      }));
      heroArticles.value = articles.value.slice(0, 4).map(a => ({
        slug: a.slug, title: a.title, coverImage: a.coverImage, categoryName: a.categoryName,
      }));
    }
    // Update stats
    const elA = document.getElementById('stat-articles');
    const elC = document.getElementById('stat-cats');
    if (elA) elA.textContent = String(json.data?.total || 0);
    try {
      const cr = await fetch('/api/knowledge/category/tree');
      const cj = await cr.json();
      if (cj.code === '200' && elC) elC.textContent = String(cj.data?.length || 0);
    } catch { /* */ }
  } catch { /* */ }
  loading.value = false;
});
</script>