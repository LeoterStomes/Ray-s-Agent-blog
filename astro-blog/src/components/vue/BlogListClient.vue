<template>
  <div class="flex gap-8 max-lg:flex-col">
    <!-- Sidebar -->
    <aside class="w-[220px] flex-shrink-0 max-lg:w-full">
      <div class="glass-card p-4 sticky top-24">
        <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">分类</h3>
        <nav class="space-y-0.5">
          <a
            v-for="cat in categories" :key="cat.name"
            :href="`/blog?category=${encodeURIComponent(cat.name)}`"
            :class="['flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors', currentCategory === cat.name ? 'bg-brand-50 text-brand-600 font-medium' : 'text-gray-600 hover:bg-gray-50']"
          >
            <span>{{ cat.label }}</span>
            <span class="text-xs text-gray-400">{{ cat.count }}</span>
          </a>
        </nav>
      </div>
    </aside>

    <!-- Article List -->
    <div class="flex-1 min-w-0">
      <div v-if="loading" class="text-center py-20 text-gray-400">加载中...</div>
      <div v-else-if="articles.length === 0" class="text-center py-20 glass-card">
        <p class="text-gray-400 text-lg mb-2">暂无文章</p>
        <a href="/blog" class="text-brand-600 hover:text-brand-700 text-sm">查看全部文章</a>
      </div>
      <div v-else class="space-y-5">
        <a
          v-for="a in articles" :key="a.id"
          :href="`/blog/${a.id}`"
          class="glass-card flex h-[180px] overflow-hidden group no-underline max-sm:flex-col max-sm:h-auto"
        >
          <!-- Cover Image -->
          <div class="w-[240px] h-full flex-shrink-0 relative overflow-hidden max-sm:w-full max-sm:h-[150px]">
            <img
              :src="a.coverImage || `https://picsum.photos/seed/${a.slug}/800/400`"
              :alt="a.title"
              class="w-full h-full object-cover transition-transform duration-400 group-hover:scale-105"
              loading="lazy"
              @error="(e) => { (e.target as HTMLImageElement).style.display = 'none' }"
            />
            <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <span class="text-white text-sm font-medium">阅读全文</span>
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 p-4 flex flex-col justify-between min-w-0">
            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="text-[11px] px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 font-medium">{{ a.categoryName }}</span>
                <span class="text-[11px] text-gray-400">约{{ Math.max(1, Math.ceil((a.content?.length || 0) / 300)) }}分钟阅读</span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 leading-relaxed group-hover:text-brand-600 transition-colors">{{ a.title }}</h3>
              <p class="text-sm text-gray-500 leading-relaxed line-clamp-2">{{ a.summary || '' }}</p>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-400 mt-3">
              <span>{{ formatDate(a.publishedAt) }}</span>
            </div>
          </div>
        </a>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-10">
        <a v-if="currentPageNum > 1" :href="pageUrl(currentPageNum - 1)" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors">上一页</a>
        <a v-for="n in totalPages" :key="n" :href="pageUrl(n)" :class="['w-9 h-9 rounded-lg text-sm flex items-center justify-center transition-colors', n === currentPageNum ? 'bg-brand-600 text-white font-medium' : 'text-gray-600 hover:bg-gray-100']">{{ n }}</a>
        <a v-if="currentPageNum < totalPages" :href="pageUrl(currentPageNum + 1)" class="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors">下一页</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const articles = ref<any[]>([]);
const categories = ref<any[]>([]);
const loading = ref(true);
const totalPages = ref(1);
const totalArticles = ref(0);

const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
const currentCategory = params.get('category') || '全部';
const currentTag = params.get('tag') || '';
const currentPageNum = parseInt(params.get('page') || '1');

function pageUrl(n: number) {
  const p = new URLSearchParams(window.location.search);
  p.set('page', String(n));
  return `/blog?${p.toString()}`;
}

function formatDate(d: string | Date) {
  if (!d) return '';
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
}

onMounted(async () => {
  try {
    const pageSize = 6;
    let url = `/api/knowledge/article/page?status=1&size=${pageSize}&currentPage=${currentPageNum}`;
    if (currentCategory !== '全部') url += `&categoryId=${currentCategory}`;
    if (currentTag) url += `&keyword=${encodeURIComponent(currentTag)}`;

    const res = await fetch(url);
    const json = await res.json();
    if (json.code === '200' && json.data) {
      articles.value = (json.data.records || []).map((r: any) => ({
        id: r.id,
        title: r.title,
        slug: r.id,
        summary: r.summary,
        content: r.content,
        coverImage: r.coverImage,
        categoryName: r.categoryName,
        tags: r.tags ? r.tags.split(',').filter(Boolean) : [],
        readCount: r.readCount || 0,
        publishedAt: r.publishedAt,
      }));
      totalPages.value = json.data.pages || 1;
      totalArticles.value = json.data.total || 0;
      // Update title count
      const el = document.getElementById('total-articles');
      if (el) el.textContent = String(totalArticles.value);
    }
  } catch { /* */ }
  loading.value = false;

  try {
    const cr = await fetch('/api/knowledge/category/tree');
    const cj = await cr.json();
    if (cj.code === '200' && cj.data) {
      categories.value = [
        { name: '全部', label: '全部', count: totalArticles.value },
        ...cj.data.map((c: any) => ({ name: String(c.id), label: c.categoryName, count: c.articleCount })),
      ];
    }
  } catch { /* */ }
});
</script>