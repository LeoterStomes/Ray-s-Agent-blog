<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-700">音乐管理</h2>
      <label class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors cursor-pointer">
        + 上传音乐
        <input type="file" accept="audio/*" class="hidden" @change="upload" />
      </label>
    </div>
    <div class="bg-white/80 backdrop-blur rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50/80 text-gray-500"><tr>
          <th class="text-left px-4 py-3 font-medium">标题</th><th class="text-left px-4 py-3 font-medium w-28">艺术家</th><th class="text-left px-4 py-3 font-medium w-16">排序</th><th class="text-right px-4 py-3 font-medium w-40">操作</th>
        </tr></thead>
        <tbody class="divide-y">
          <tr v-for="m in items" :key="m.id" class="hover:bg-gray-50/50">
            <td class="px-4 py-3 text-gray-800">{{ m.title }}</td>
            <td class="px-4 py-3 text-gray-500">{{ m.artist }}</td>
            <td class="px-4 py-3 text-gray-500">{{ m.sort_order }}</td>
            <td class="px-4 py-3 text-right">
              <button @click="openLyrics(m)" class="text-xs text-brand-600 hover:text-brand-700 mr-2">歌词</button>
              <button @click="remove(m.id)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="items.length === 0" class="text-center py-12 text-gray-400 text-sm">暂无音乐，上传一首吧</div>
    </div>

    <!-- Lyrics Dialog -->
    <div v-if="lyricsShow" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="lyricsShow=false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold mb-4">{{ lyricsTarget?.title }} - 歌词</h2>
        <textarea v-model="lyricsText" placeholder="粘贴 LRC 歌词或纯文本..." rows="12" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500 font-mono" />
        <div class="flex justify-end gap-2 mt-4">
          <button @click="lyricsShow=false" class="px-4 py-2 border rounded-lg text-sm text-gray-600">取消</button>
          <button @click="saveLyrics" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg">保存</button>
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
const lyricsShow = ref(false);
const lyricsTarget = ref<any>(null);
const lyricsText = ref('');

onMounted(async () => { const r = await api('/api/music/list'); items.value = r?.data || []; });

async function upload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const raw = file.name.replace(/\.[^.]+$/, '');
  let title = raw, artist = '';
  if (raw.includes(' - ')) {
    const parts = raw.split(' - ');
    artist = parts[0].trim();
    title = parts.slice(1).join(' - ').trim();
  }
  const fd = new FormData(); fd.append('file', file); fd.append('title', title); fd.append('artist', artist);
  await fetch('/api/music/upload', { method: 'POST', headers: { token: getToken() || '' }, body: fd });
  (e.target as HTMLInputElement).value = '';
  const r = await api('/api/music/list'); items.value = r?.data || [];
}

function openLyrics(m: any) { lyricsTarget.value = m; lyricsText.value = m.lyrics || ''; lyricsShow.value = true; }
async function saveLyrics() {
  if (!lyricsTarget.value) return;
  await api(`/api/music/${lyricsTarget.value.id}`, { method: 'PUT', body: JSON.stringify({ lyrics: lyricsText.value }) });
  lyricsShow.value = false;
  const r = await api('/api/music/list'); items.value = r?.data || [];
}
async function remove(id: number) { if (confirm('确定删除？')) { await api(`/api/music/${id}`, { method: 'DELETE' }); const r = await api('/api/music/list'); items.value = r?.data || []; } }
</script>