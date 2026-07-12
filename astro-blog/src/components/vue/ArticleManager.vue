<template>
  <div>
    <!-- Toolbar -->
    <div class="flex items-center justify-between mb-4">
      <input v-model="search" @input="load" placeholder="搜索文章..." class="px-4 py-2 border rounded-lg text-sm w-64 outline-none focus:ring-2 focus:ring-brand-500" />
      <div class="flex gap-2">
        <select v-model="statusFilter" @change="load" class="px-3 py-2 border rounded-lg text-sm outline-none">
          <option value="">全部状态</option>
          <option value="1">已发布</option>
          <option value="0">草稿</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="text-left px-4 py-3 font-medium">标题</th>
            <th class="text-left px-4 py-3 font-medium w-24">分类</th>
            <th class="text-left px-4 py-3 font-medium w-20">状态</th>
            <th class="text-left px-4 py-3 font-medium w-28">发布时间</th>
            <th class="text-right px-4 py-3 font-medium w-40">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="a in articles" :key="a.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-gray-800 truncate max-w-xs">{{ a.title }}</td>
            <td class="px-4 py-3 text-gray-500">{{ a.categoryName || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="a.status === 1 ? 'text-green-600 bg-green-50' : 'text-gray-500 bg-gray-100'" class="text-xs px-2 py-0.5 rounded-full">{{ a.status === 1 ? '已发布' : '草稿' }}</span>
            </td>
            <td class="px-4 py-3 text-gray-400">{{ formatDate(a.publishedAt) }}</td>
            <td class="px-4 py-3 text-right">
              <button @click="openEditor(a)" class="text-xs text-brand-600 hover:text-brand-700 mr-2">编辑</button>
              <button v-if="a.status !== 1" @click="publish(a.id)" class="text-xs text-green-600 hover:text-green-700 mr-2">发布</button>
              <button v-else @click="offline(a.id)" class="text-xs text-orange-500 hover:text-orange-600 mr-2">下架</button>
              <button @click="remove(a.id)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="articles.length === 0" class="text-center py-12 text-gray-400 text-sm">暂无文章</div>
    </div>

    <!-- Editor Modal -->
    <div v-if="editing" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="editing = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-auto p-6">
        <h2 class="text-lg font-bold mb-4">{{ editId ? '编辑文章' : '新建文章' }}</h2>
        <div class="space-y-3">
          <input v-model="form.title" placeholder="标题" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <select v-model="form.categoryId" class="w-full px-4 py-2 border rounded-lg text-sm outline-none">
            <option :value="0">选择分类</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.categoryName }}</option>
          </select>
          <input v-model="form.tags" placeholder="标签 (逗号分隔)" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <textarea v-model="form.summary" placeholder="摘要" rows="2" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <div class="flex items-center gap-2 mb-1">
            <button type="button" @click="preview = false" :class="!preview ? 'text-brand-600 font-medium' : 'text-gray-400'" class="text-xs">编辑</button>
            <button type="button" @click="preview = true" :class="preview ? 'text-brand-600 font-medium' : 'text-gray-400'" class="text-xs">预览</button>
          </div>
          <textarea v-if="!preview" v-model="form.content" placeholder="内容 (支持 HTML/Markdown)" rows="10" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500 font-mono" />
          <div v-else class="w-full px-4 py-2 border rounded-lg text-sm min-h-[200px] prose prose-sm max-w-none" v-html="form.content || '<p class=text-gray-400>暂无内容</p>'" />
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="editing = false" class="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">取消</button>
          <button @click="save" :disabled="saving" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getToken } from '@lib/auth';

const api = (url: string, opts?: RequestInit) =>
  fetch(url, { ...opts, headers: { ...opts?.headers, token: getToken() || '', 'Content-Type': 'application/json' } }).then(r => r.json());

const articles = ref<any[]>([]);
const categories = ref<any[]>([]);
const search = ref('');
const statusFilter = ref('');
const editing = ref(false);
const preview = ref(false);
const editId = ref<string | null>(null);
const saving = ref(false);
const form = ref({ title: '', categoryId: 0, tags: '', summary: '', content: '' });

onMounted(() => { load(); loadCategories(); });

async function load() {
  const params = new URLSearchParams({ size: '50' });
  if (search.value) params.set('keyword', search.value);
  if (statusFilter.value !== '') params.set('status', statusFilter.value);
  else params.set('status', '');
  const r = await api(`/api/knowledge/article/page?${params}`);
  articles.value = r?.data?.records || [];
}

async function loadCategories() {
  const r = await api('/api/knowledge/category/tree');
  categories.value = r?.data || [];
}

async function openEditor(article?: any) {
  if (article) {
    editId.value = article.id;
    // Fetch full article detail to get content
    const detail = await api(`/api/knowledge/article/${article.id}`);
    const d = detail?.data || article;
    form.value = { title: d.title, categoryId: d.categoryId || 0, tags: (d.tags || '').replace(/,/g, ', '), summary: d.summary || '', content: d.content || '' };
  } else {
    editId.value = null;
    form.value = { title: '', categoryId: 0, tags: '', summary: '', content: '' };
  }
  preview.value = false;
  editing.value = true;
}

async function save() {
  saving.value = true;
  // Auto-format content before saving
  let content = form.value.content;
  content = content.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  content = content.replace(/<p>\s*<\/p>/g, '');
  content = content.replace(/\n{3,}/g, '\n\n');
  const body = { ...form.value, tags: form.value.tags.split(/[,，]/).map(t => t.trim()).filter(Boolean).join(','), content };
  if (editId.value) {
    await api(`/api/knowledge/article/${editId.value}`, { method: 'PUT', body: JSON.stringify(body) });
  } else {
    await api('/api/knowledge/article', { method: 'POST', body: JSON.stringify(body) });
  }
  saving.value = false;
  editing.value = false;
  load();
}

async function publish(id: string) { await api(`/api/knowledge/article/${id}/publish`, { method: 'POST' }); load(); }
async function offline(id: string) { await api(`/api/knowledge/article/${id}/offline`, { method: 'POST' }); load(); }
async function remove(id: string) { if (confirm('确定删除？')) { await api(`/api/knowledge/article/${id}`, { method: 'DELETE' }); load(); } }

function formatDate(d: string) { return d ? new Date(d).toLocaleDateString('zh-CN') : '-'; }
</script>
