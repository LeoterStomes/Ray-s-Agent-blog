<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-700">知识库管理</h2>
        <p class="text-xs text-gray-400 mt-0.5">导入外部文档作为 AI 参考库，支持 PDF / DOCX / TXT / MD</p>
      </div>
      <div class="flex gap-2">
        <button @click="rebuild" :disabled="rebuilding" class="px-4 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50">
          {{ rebuilding ? '重建中...' : '重建博客索引' }}
        </button>
        <label class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors cursor-pointer">
          + 导入文档
          <input type="file" accept=".pdf,.docx,.txt,.md" class="hidden" @change="upload" />
        </label>
      </div>
    </div>

    <!-- 提示 -->
    <div class="bg-blue-50/80 border border-blue-200 rounded-lg px-4 py-3 mb-4 text-sm text-blue-700 flex items-start gap-2">
      <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span>导入的文档会自动切片并向量化，AI 可通过「搜索知识库」工具查询。适合导入技术规范、官方文档、参考资料等。</span>
    </div>

    <!-- 文档列表 -->
    <div class="bg-white/80 backdrop-blur rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50/80 text-gray-500"><tr>
          <th class="text-left px-4 py-3 font-medium">文档名称</th>
          <th class="text-right px-4 py-3 font-medium w-32">操作</th>
        </tr></thead>
        <tbody class="divide-y">
          <tr v-for="doc in docs" :key="doc.filename" class="hover:bg-gray-50/50">
            <td class="px-4 py-3 text-gray-800 flex items-center gap-2">
              <span>{{ docIcon(doc.filename) }}</span>
              <span>{{ doc.filename }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <button @click="remove(doc.filename)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="docs.length === 0" class="text-center py-12 text-gray-400 text-sm">
        暂无外部文档，点击「导入文档」上传
      </div>
    </div>

    <!-- 重建结果 -->
    <div v-if="rebuildMsg" class="mt-3 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ rebuildMsg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getToken } from '@lib/auth';

const docs = ref<{ filename: string }[]>([]);
const rebuilding = ref(false);
const rebuildMsg = ref('');

function headers(): Record<string, string> {
  const token = getToken() || '';
  return { token, 'Content-Type': 'application/json' };
}

function docIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return '📄';
  if (ext === 'docx') return '📝';
  if (ext === 'md') return '📋';
  return '📃';
}

async function fetchDocs() {
  try {
    const resp = await fetch('/api/rag/documents', { headers: headers() });
    const json = await resp.json();
    if (json.code === '200') docs.value = json.data || [];
  } catch {}
}

async function upload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const resp = await fetch('/api/rag/import/upload', {
      method: 'POST',
      headers: { token: getToken() || '' },
      body: form,
    });
    const json = await resp.json();
    alert(json.msg || '导入完成');
    fetchDocs();
  } catch {
    alert('上传失败');
  }
  (e.target as HTMLInputElement).value = '';
}

async function remove(filename: string) {
  if (!confirm(`确认删除「${filename}」？`)) return;
  try {
    const resp = await fetch(`/api/rag/documents/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
      headers: headers(),
    });
    const json = await resp.json();
    alert(json.msg || '删除完成');
    fetchDocs();
  } catch {
    alert('删除失败');
  }
}

async function rebuild() {
  if (!confirm('将重新解析所有已发布文章并重建索引，确认？')) return;
  rebuilding.value = true;
  rebuildMsg.value = '';
  try {
    const resp = await fetch('/api/rag/reindex', { method: 'POST', headers: headers() });
    const json = await resp.json();
    rebuildMsg.value = json.msg || '完成';
  } catch {
    rebuildMsg.value = '重建失败';
  } finally {
    rebuilding.value = false;
  }
}

onMounted(fetchDocs);
</script>