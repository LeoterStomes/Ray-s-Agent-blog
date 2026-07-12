<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-700">公告管理</h2>
      <button @click="openDialog()" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors">+ 新建公告</button>
    </div>

    <div class="bg-white/80 backdrop-blur rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50/80 text-gray-500">
          <tr>
            <th class="text-left px-4 py-3 font-medium">内容</th>
            <th class="text-left px-4 py-3 font-medium w-36">链接</th>
            <th class="text-left px-4 py-3 font-medium w-16">排序</th>
            <th class="text-left px-4 py-3 font-medium w-16">状态</th>
            <th class="text-right px-4 py-3 font-medium w-32">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="a in items" :key="a.id" class="hover:bg-gray-50/50">
            <td class="px-4 py-3 text-gray-800">{{ a.content }}</td>
            <td class="px-4 py-3 text-gray-400 truncate max-w-[140px]">{{ a.link || '-' }}</td>
            <td class="px-4 py-3 text-gray-500">{{ a.sort_order }}</td>
            <td class="px-4 py-3">
              <span :class="a.status === 1 ? 'text-green-600' : 'text-gray-400'" class="text-xs">{{ a.status === 1 ? '显示' : '隐藏' }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <button @click="openDialog(a)" class="text-xs text-brand-600 hover:text-brand-700 mr-2">编辑</button>
              <button @click="remove(a.id)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Dialog -->
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="show = false">
      <div class="bg-white rounded-2xl shadow-2xl w-96 p-6">
        <h2 class="text-lg font-bold mb-4">{{ editId ? '编辑公告' : '新建公告' }}</h2>
        <div class="space-y-3">
          <textarea v-model="form.content" placeholder="公告内容" rows="3" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <input v-model="form.link" placeholder="链接（可选）如 /blog/post-xxx" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <input v-model.number="form.sort_order" type="number" placeholder="排序" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="show = false" class="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">取消</button>
          <button @click="save" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800">{{ saving ? '保存中...' : '保存' }}</button>
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

const items = ref<any[]>([]);
const show = ref(false);
const editId = ref<number | null>(null);
const saving = ref(false);
const form = ref({ content: '', link: '', sort_order: 0 });

onMounted(load);

async function load() {
  const r = await api('/api/announcement/all');
  items.value = r?.data || [];
}

function openDialog(a?: any) {
  if (a) {
    editId.value = a.id;
    form.value = { content: a.content, link: a.link || '', sort_order: a.sort_order || 0 };
  } else {
    editId.value = null;
    form.value = { content: '', link: '', sort_order: 0 };
  }
  show.value = true;
}

async function save() {
  saving.value = true;
  if (editId.value) {
    await api(`/api/announcement/${editId.value}`, { method: 'PUT', body: JSON.stringify(form.value) });
  } else {
    await api('/api/announcement', { method: 'POST', body: JSON.stringify(form.value) });
  }
  saving.value = false;
  show.value = false;
  load();
}

async function remove(id: number) {
  if (confirm('确定删除？')) { await api(`/api/announcement/${id}`, { method: 'DELETE' }); load(); }
}
</script>