<template>
  <div class="tool-result-card">
    <!-- 导出文件下载（优先） -->
    <template v-if="isExportFile">
      <div class="export-card">
        <div class="export-icon">
          <svg v-if="result.format==='pdf'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
          <svg v-else-if="result.format==='docx'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </div>
        <div class="export-info">
          <div class="export-filename">{{ result.filename || result.title }}</div>
          <div class="export-format">{{ (result.format||'').toUpperCase() }} 文件</div>
        </div>
        <a :href="encodeURI(result.url)" :download="result.filename" class="export-dl-btn">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
          下载
        </a>
      </div>
    </template>
    <!-- 文章列表 -->
    <template v-else-if="isArticleList">
      <div class="result-header">{{ result.articles?.length || 0 }} 篇文章</div>
      <a
        v-for="a in result.articles"
        :key="a.id"
        :href="a.url || `/blog/${a.id}`"
        class="article-item"
      >
        <div class="article-title">{{ a.title }}</div>
        <div class="article-meta">
          <span v-if="a.category" class="article-category">{{ a.category }}</span>
          <span v-if="a.published_at" class="article-date">{{ formatDate(a.published_at) }}</span>
        </div>
        <div v-if="a.summary" class="article-summary">{{ truncate(a.summary, 80) }}</div>
      </a>
    </template>
    <!-- 分类列表 -->
    <template v-else-if="result.categories">
      <div class="result-header">分类列表</div>
      <div class="category-tags">
        <span v-for="c in result.categories" :key="c.id" class="category-tag">
          {{ c.name }} ({{ c.article_count }})
        </span>
      </div>
    </template>
    <!-- 单篇文章详情 -->
    <template v-else-if="result.title && result.content">
      <div class="result-header">{{ result.title }}</div>
      <div class="article-summary">{{ truncate(result.content, 150) }}</div>
      <a :href="result.url || `/blog/${result.id}`" class="read-more">阅读全文 →</a>
    </template>
    <!-- 网页搜索结果 -->
    <template v-else-if="result.results">
      <div class="result-header">搜索结果</div>
      <div class="web-results">{{ truncate(result.results, 200) }}</div>
    </template>
    <!-- 计数结果 -->
    <template v-else-if="typeof result.count === 'number'">
      <div class="result-header">找到 {{ result.count }} 条结果</div>
    </template>
    <!-- 其他 -->
    <template v-else>
      <div class="result-header">工具执行完成</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ result: any }>();

const isArticleList = computed(() => props.result?.articles?.length >= 0);
const isExportFile = computed(() => {
  const fmt = (props.result?.format || '').toLowerCase().trim();
  const url = props.result?.url || '';
  const fname = props.result?.filename || '';
  // 有完整导出信息
  if (url && fname && ['pdf','docx','txt'].includes(fmt)) return true;
  // 兜底：URL 匹配导出文件
  return /\/uploads\/export\/[^\s]+\.(pdf|docx|txt)$/i.test(url);
});

function formatDate(d: string): string {
  if (!d) return '';
  return d.slice(0, 10);
}
function truncate(s: string, n: number): string {
  if (!s) return '';
  return s.length > n ? s.slice(0, n) + '...' : s;
}
</script>

<style scoped>
.tool-result-card {
  margin: 4px 0;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 12px;
}
.result-header {
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  font-size: 12px;
}
.article-item {
  display: block;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
}
.article-item:last-child { border-bottom: none; }
.article-item:hover { background: #f1f5f9; margin: 0 -4px; padding: 6px 4px; border-radius: 4px; }
.article-title {
  font-weight: 500;
  color: #1e293b;
}
.article-meta {
  display: flex;
  gap: 8px;
  margin-top: 2px;
}
.article-category {
  color: #5b7bff;
  font-size: 11px;
}
.article-date { color: #94a3b8; font-size: 11px; }
.article-summary {
  color: #94a3b8;
  margin-top: 2px;
  line-height: 1.4;
}
.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.category-tag {
  padding: 2px 8px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 12px;
  font-size: 11px;
}
.read-more {
  display: inline-block;
  margin-top: 6px;
  color: #5b7bff;
  text-decoration: none;
  font-weight: 500;
}
.web-results {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
  color: #64748b;
  font-size: 11px;
}

/* Export download card */
.export-card {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 10px; margin-top: 4px;
}
.export-icon { color: #16a34a; flex-shrink: 0; }
.export-info { flex: 1; min-width: 0; }
.export-filename { font-size: 12px; font-weight: 600; color: #166534; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.export-format { font-size: 10px; color: #65a30d; }
.export-dl-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 14px; background: #16a34a; color: #fff;
  border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600;
  flex-shrink: 0; transition: background .15s;
}
.export-dl-btn:hover { background: #15803d; }
</style>
