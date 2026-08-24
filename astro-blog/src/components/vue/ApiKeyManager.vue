<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-700">API Key 管理</h2>
        <p class="text-xs text-gray-400 mt-0.5">管理所有 API 密钥和配置项。修改后需重启后端生效。</p>
      </div>
    </div>

    <!-- 按分组 -->
    <div v-for="group in groups" :key="group" class="mb-6">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{{ group }}</h3>
      <div class="bg-white/80 backdrop-blur rounded-xl shadow-sm overflow-hidden">
        <div v-for="item in itemsByGroup(group)" :key="item.key" class="flex items-center gap-4 px-4 py-3 border-b last:border-b-0 hover:bg-gray-50/50">
          <div class="flex-1 min-w-0">
            <div class="text-sm text-gray-700 font-medium">{{ item.label }}</div>
            <div class="text-xs text-gray-400 font-mono truncate">{{ item.key }}</div>
          </div>
          <div class="flex items-center gap-2">
            <input
              v-if="editing[item.key]"
              v-model="editValues[item.key]"
              class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-64 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
              :placeholder="item.is_sensitive ? '输入新值...' : '输入值...'"
            />
            <span v-else class="text-sm text-gray-500 font-mono max-w-[200px] truncate">{{ item.value || '(未设置)' }}</span>
            <button
              v-if="!editing[item.key]"
              @click="startEdit(item)"
              class="text-xs text-brand-600 hover:text-brand-700 px-2 py-1"
            >编辑</button>
            <template v-else>
              <button @click="save(item)" class="text-xs text-green-600 hover:text-green-700 px-2 py-1">保存</button>
              <button @click="cancelEdit(item)" class="text-xs text-gray-400 hover:text-gray-600 px-2 py-1">取消</button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div v-if="msg" class="mt-4 px-4 py-2 rounded-lg text-sm" :class="msgType === 'ok' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'">
      {{ msg }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { getToken } from '@lib/auth';

interface ApiKeyItem {
  key: string; label: string; group: string; value: string; is_sensitive: boolean;
}

const items = ref<ApiKeyItem[]>([]);
const editing = ref<Record<string, boolean>>({});
const editValues = ref<Record<string, string>>({});
const msg = ref('');
const msgType = ref('ok');

const groups = computed(() => [...new Set(items.value.map(i => i.group))]);
function itemsByGroup(group: string) { return items.value.filter(i => i.group === group); }

function headers(): Record<string, string> {
  return { token: getToken() || '', 'Content-Type': 'application/json' };
}

onMounted(async () => {
  try {
    const resp = await fetch('/api/admin/api-keys', { headers: headers() });
    const json = await resp.json();
    if (json.code === '200') items.value = json.data.items || [];
  } catch {}
});

function startEdit(item: ApiKeyItem) {
  editing.value[item.key] = true;
  editValues.value[item.key] = item.is_sensitive ? '' : item.value;
}

function cancelEdit(item: ApiKeyItem) {
  editing.value[item.key] = false;
  delete editValues.value[item.key];
}

async function save(item: ApiKeyItem) {
  const val = editValues.value[item.key] || '';
  try {
    const resp = await fetch('/api/admin/api-keys', {
      method: 'PUT', headers: headers(),
      body: JSON.stringify({ key: item.key, value: val }),
    });
    const json = await resp.json();
    if (json.code === '200') {
      item.value = item.is_sensitive ? '***' + val.slice(-4) : val;
      msg.value = json.msg;
      msgType.value = 'ok';
    } else {
      msg.value = json.msg || '更新失败';
      msgType.value = 'error';
    }
    cancelEdit(item);
    setTimeout(() => { msg.value = ''; }, 3000);
  } catch {
    msg.value = '网络错误';
    msgType.value = 'error';
  }
}
</script>
