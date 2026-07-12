<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-700">分类管理</h2>
      <button @click="openDialog()" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors">+ 新建分类</button>
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="text-left px-4 py-3 font-medium">名称</th>
            <th class="text-left px-4 py-3 font-medium">描述</th>
            <th class="text-left px-4 py-3 font-medium w-16">排序</th>
            <th class="text-right px-4 py-3 font-medium w-32">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="c in categories" :key="c.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-gray-800">{{ c.categoryName }}</td>
            <td class="px-4 py-3 text-gray-500">{{ c.description || '-' }}</td>
            <td class="px-4 py-3 text-gray-500">{{ c.sortOrder }}</td>
            <td class="px-4 py-3 text-right">
              <button @click="openDialog(c)" class="text-xs text-brand-600 hover:text-brand-700 mr-2">编辑</button>
              <button @click="remove(c.id)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Dialog -->
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="show = false">
      <div class="bg-white rounded-2xl shadow-2xl w-96 p-6">
        <h2 class="text-lg font-bold mb-4">{{ editId ? '编辑分类' : '新建分类' }}</h2>
        <div class="space-y-3">
          <input v-model="form.categoryName" placeholder="名称" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <input v-model="form.description" placeholder="描述" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
          <input v-model.number="form.sortOrder" type="number" placeholder="排序" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
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

const categories = ref<any[]>([]);
const show = ref(false);
const editId = ref<number | null>(null);
const saving = ref(false);
const form = ref({ categoryName: '', description: '', sortOrder: 0 });

onMounted(load);

async function load() {
  const r = await api('/api/knowledge/category/tree');
  categories.value = r?.data || [];
}

function openDialog(c?: any) {
  if (c) {
    editId.value = c.id;
    form.value = { categoryName: c.categoryName, description: c.description || '', sortOrder: c.sortOrder || 0 };
  } else {
    editId.value = null;
    form.value = { categoryName: '', description: '', sortOrder: 0 };
  }
  show.value = true;
}

async function save() {
  saving.value = true;
  if (editId.value) {
    await api(`/api/knowledge/category/${editId.value}`, { method: 'PUT', body: JSON.stringify(form.value) });
  } else {
    await api('/api/knowledge/category', { method: 'POST', body: JSON.stringify(form.value) });
  }
  saving.value = false;
  show.value = false;
  load();
}

async function remove(id: number) {
  if (confirm('确定删除？')) { await api(`/api/knowledge/category/${id}`, { method: 'DELETE' }); load(); }
}
</script>
