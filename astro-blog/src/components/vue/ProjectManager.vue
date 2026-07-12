<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-700">项目管理</h2>
      <button @click="openDialog()" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors">+ 导入项目</button>
    </div>

    <div class="bg-white/80 backdrop-blur rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50/80 text-gray-500"><tr>
          <th class="text-left px-4 py-3 font-medium">名称</th><th class="text-left px-4 py-3 font-medium">标签</th><th class="text-left px-4 py-3 font-medium w-32">GitHub</th><th class="text-right px-4 py-3 font-medium w-32">操作</th>
        </tr></thead>
        <tbody class="divide-y">
          <tr v-for="p in items" :key="p.id" class="hover:bg-gray-50/50">
            <td class="px-4 py-3 text-gray-800 font-medium">{{ p.name }}</td>
            <td class="px-4 py-3">
              <span v-for="t in (p.tags||'').split(',').filter(Boolean)" :key="t" class="text-[10px] px-1.5 py-0.5 rounded-full bg-brand-50 text-brand-600 mr-1">{{ t.trim() }}</span>
            </td>
            <td class="px-4 py-3">
              <a v-if="p.github_url" :href="p.github_url" target="_blank" class="text-brand-600 hover:underline text-xs">查看</a>
              <span v-else class="text-gray-300">-</span>
            </td>
            <td class="px-4 py-3 text-right">
              <button @click="openDialog(p)" class="text-xs text-brand-600 hover:text-brand-700 mr-2">编辑</button>
              <button @click="remove(p.id)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Dialog -->
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="show=false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold mb-4">{{ editId ? '编辑项目' : '导入项目' }}</h2>
        <div class="space-y-3">
          <input v-model="form.github_url" placeholder="GitHub URL (可选，如 https://github.com/user/repo)" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" @blur="autoName" />
          <input v-model="form.name" placeholder="项目名称" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <div class="flex items-center gap-2">
            <textarea v-model="form.description" placeholder="项目介绍 (填 GitHub URL 自动拉取 README)" rows="4" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500 flex-1" />
            <label class="px-3 py-2 border rounded-lg text-xs text-gray-500 hover:bg-gray-50 cursor-pointer flex-shrink-0" title="导入 MD 文件">
              导入MD
              <input type="file" accept=".md,.txt" class="hidden" @change="importMd" />
            </label>
          </div>
          <input v-model="form.tags" placeholder="标签 (逗号分隔，如: React, TypeScript, 开源)" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="show=false" class="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">取消</button>
          <button @click="save" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getToken } from '@lib/auth';

const api = (url: string, o?: RequestInit) => fetch(url, { ...o, headers: { ...o?.headers, token: getToken() || '', 'Content-Type': 'application/json' } }).then(r => r.json());
const items = ref<any[]>([]);
const show = ref(false);
const editId = ref<number | null>(null);
const saving = ref(false);
const form = ref({ name: '', description: '', tags: '', github_url: '' });

onMounted(async () => { const r = await api('/api/project/all'); items.value = r?.data || []; });

let fetching = false;
async function autoName() {
  const url = form.value.github_url;
  if (!url) return;
  // Parse name from URL
  const parts = url.replace(/\/$/, '').split('/');
  if (!form.value.name && parts.length >= 2) {
    form.value.name = `${parts[parts.length - 2]}/${parts[parts.length - 1]}`;
  }
  // Fetch README summary
  if (fetching) return;
  fetching = true;
  try {
    const r = await fetch(`/api/project/fetch-readme?url=${encodeURIComponent(url)}`);
    const j = await r.json();
    if (j.code === '200' && j.data) {
      if (!form.value.description) form.value.description = j.data.summary;
      if (!form.value.name) form.value.name = j.data.name;
    }
  } catch { /* */ }
  fetching = false;
}

function importMd(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const text = reader.result as string;
    // Extract first 2-3 meaningful lines as summary
    const lines = text.replace(/#/g, '').split('\n').filter(l => l.trim().length > 15).slice(0, 3);
    const summary = lines.join(' ').slice(0, 400);
    if (!form.value.description) form.value.description = summary;
  };
  reader.readAsText(file);
}

function openDialog(p?: any) {
  if (p) {
    editId.value = p.id;
    form.value = { name: p.name, description: p.description || '', tags: p.tags || '', github_url: p.github_url || '' };
  } else {
    editId.value = null;
    form.value = { name: '', description: '', tags: '', github_url: '' };
  }
  show.value = true;
}

async function save() {
  saving.value = true;
  if (editId.value) {
    await api(`/api/project/${editId.value}`, { method: 'PUT', body: JSON.stringify(form.value) });
  } else {
    await api('/api/project', { method: 'POST', body: JSON.stringify(form.value) });
  }
  saving.value = false; show.value = false;
  const r = await api('/api/project/all'); items.value = r?.data || [];
}

async function remove(id: number) {
  if (confirm('确定删除？')) { await api(`/api/project/${id}`, { method: 'DELETE' }); const r = await api('/api/project/all'); items.value = r?.data || []; }
}
</script>