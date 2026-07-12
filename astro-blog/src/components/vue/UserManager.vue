<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <input v-model="search" @input="load" placeholder="搜索用户..." class="px-4 py-2 border rounded-lg text-sm w-64 outline-none focus:ring-2 focus:ring-brand-500" />
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="text-left px-4 py-3 font-medium">ID</th>
            <th class="text-left px-4 py-3 font-medium">用户名</th>
            <th class="text-left px-4 py-3 font-medium">昵称</th>
            <th class="text-left px-4 py-3 font-medium">邮箱</th>
            <th class="text-left px-4 py-3 font-medium w-20">角色</th>
            <th class="text-left px-4 py-3 font-medium w-20">状态</th>
            <th class="text-right px-4 py-3 font-medium w-24">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="u in users" :key="u.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-gray-400">{{ u.id }}</td>
            <td class="px-4 py-3 text-gray-800">{{ u.username }}</td>
            <td class="px-4 py-3 text-gray-600">{{ u.nickname || '-' }}</td>
            <td class="px-4 py-3 text-gray-500">{{ u.email || '-' }}</td>
            <td class="px-4 py-3">
              <span class="text-xs px-2 py-0.5 rounded-full" :class="roleBadge(u.userType)">{{ roleName(u.userType) }}</span>
            </td>
            <td class="px-4 py-3">
              <span :class="u.status === 1 ? 'text-green-600' : 'text-red-500'" class="text-xs">{{ u.status === 1 ? '正常' : '禁用' }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <button @click="toggleStatus(u)" class="text-xs" :class="u.status === 1 ? 'text-red-500 hover:text-red-600' : 'text-green-600 hover:text-green-700'">
                {{ u.status === 1 ? '禁用' : '启用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getToken } from '@lib/auth';

const api = (url: string, opts?: RequestInit) =>
  fetch(url, { ...opts, headers: { ...opts?.headers, token: getToken() || '', 'Content-Type': 'application/json' } }).then(r => r.json());

const users = ref<any[]>([]);
const search = ref('');

onMounted(load);

async function load() {
  const params = new URLSearchParams({ size: '50' });
  if (search.value) params.set('username', search.value);
  const r = await api(`/api/user/page?${params}`);
  users.value = r?.data?.records || [];
}

function roleName(t: number) {
  if (t === 2) return '管理员';
  if (t === 3) return '医生';
  return '用户';
}
function roleBadge(t: number) {
  if (t === 2) return 'bg-purple-50 text-purple-600';
  return 'bg-gray-100 text-gray-500';
}

async function toggleStatus(u: any) {
  const newStatus = u.status === 1 ? 0 : 1;
  await api(`/api/user/${u.id}/status?status=${newStatus}`, { method: 'PUT' });
  load();
}
</script>