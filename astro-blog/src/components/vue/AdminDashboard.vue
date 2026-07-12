<template>
  <div>
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="text-3xl font-bold text-gray-800">{{ stats.articles }}</div>
        <div class="text-sm text-gray-500 mt-1">文章总数</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="text-3xl font-bold text-gray-800">{{ stats.categories }}</div>
        <div class="text-sm text-gray-500 mt-1">分类</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="text-3xl font-bold text-gray-800">{{ stats.users }}</div>
        <div class="text-sm text-gray-500 mt-1">用户</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="text-3xl font-bold text-gray-800">{{ stats.visitors }}</div>
        <div class="text-sm text-gray-500 mt-1">今日访问</div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <h3 class="text-sm font-semibold text-gray-500 mb-4">最近文章</h3>
        <div v-if="loading" class="text-sm text-gray-400">加载中...</div>
        <div v-else class="space-y-2">
          <div v-for="a in articles" :key="a.id" class="flex items-center justify-between text-sm">
            <span class="text-gray-700 truncate flex-1">{{ a.title }}</span>
            <span :class="a.status === 1 ? 'text-green-500' : 'text-gray-400'" class="text-xs ml-2">{{ a.status === 1 ? '已发布' : '草稿' }}</span>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <h3 class="text-sm font-semibold text-gray-500 mb-4">最新用户</h3>
        <div v-if="loading" class="text-sm text-gray-400">加载中...</div>
        <div v-else class="space-y-2">
          <div v-for="u in users" :key="u.id" class="flex items-center justify-between text-sm">
            <span class="text-gray-700">{{ u.nickname || u.username }}</span>
            <span class="text-xs text-gray-400">{{ u.email || '-' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 背景壁纸管理 -->
    <div class="bg-white rounded-xl p-5 shadow-sm">
      <h3 class="text-sm font-semibold text-gray-500 mb-4">站点背景</h3>
      <div class="flex items-center gap-4 flex-wrap">
        <div class="w-32 h-20 rounded-lg border border-gray-200 overflow-hidden bg-gray-100 flex-shrink-0" :style="bgPreviewStyle">
          <div v-if="!bgUrl" class="w-full h-full flex items-center justify-center text-xs text-gray-400">默认渐变</div>
        </div>
        <div class="flex-1 min-w-[200px]">
          <label class="inline-block px-4 py-2 bg-brand-600 text-white text-sm rounded-lg cursor-pointer hover:bg-brand-700 transition-colors">
            {{ uploading ? '上传中...' : '选择图片' }}
            <input type="file" accept="image/*" class="hidden" @change="onFileChange" :disabled="uploading" />
          </label>
          <button v-if="bgUrl" @click="removeBg" class="ml-3 px-4 py-2 border border-red-200 text-red-500 text-sm rounded-lg hover:bg-red-50 transition-colors">恢复默认</button>
          <p class="text-xs text-gray-400 mt-2">支持 JPG / PNG / WebP，推荐 1920×1080</p>
          <p v-if="uploadMsg" class="text-xs mt-1" :class="uploadOk ? 'text-green-500' : 'text-red-500'">{{ uploadMsg }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { getToken } from '@lib/auth';

const loading = ref(true);
const stats = ref({ articles: 0, categories: 0, users: 0, visitors: 0 });
const articles = ref<any[]>([]);
const users = ref<any[]>([]);

// 背景管理
const bgUrl = ref('');
const uploading = ref(false);
const uploadMsg = ref('');
const uploadOk = ref(false);

const bgPreviewStyle = computed(() => bgUrl.value ? `background: url(${bgUrl.value}) center/cover` : '');

async function loadBg() {
  try {
    const r = await fetch('/api/site/background').then(r => r.json());
    if (r.data?.hasCustom) bgUrl.value = r.data.url;
  } catch { /* ignore */ }
}

async function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  uploadMsg.value = '';
  uploading.value = true;
  try {
    const form = new FormData();
    form.append('file', file);
    const r = await fetch('/api/site/background/upload', {
      method: 'POST',
      headers: { token: getToken() || '' },
      body: form,
    }).then(r => r.json());
    if (r.code === '200') {
      bgUrl.value = r.data.url + '?t=' + Date.now();
      uploadMsg.value = '上传成功！刷新前台页面即可看到新背景';
      uploadOk.value = true;
      // 通知其他页面刷新背景
      localStorage.setItem('_bgUrl', bgUrl.value);
    } else {
      uploadMsg.value = r.msg || '上传失败';
      uploadOk.value = false;
    }
  } catch {
    uploadMsg.value = '网络错误，请重试';
    uploadOk.value = false;
  }
  uploading.value = false;
}

async function removeBg() {
  try {
    await fetch('/api/site/background/reset', {
      method: 'POST',
      headers: { token: getToken() || '' },
    });
  } catch { /* ignore */ }
  bgUrl.value = '';
  uploadMsg.value = '已恢复默认背景';
  uploadOk.value = true;
  localStorage.removeItem('_bgUrl');
}

const API = (p: string) => fetch(p, { headers: { token: getToken() || '' } }).then(r => r.json());

onMounted(async () => {
  try {
    const [a, c, v] = await Promise.all([
      API('/api/knowledge/article/page?size=5'),
      API('/api/knowledge/category/tree'),
      API('/api/visitor/stats'),
    ]);
    articles.value = a?.data?.records || [];
    stats.value.articles = a?.data?.total || 0;
    stats.value.categories = c?.data?.length || 0;
    stats.value.visitors = v?.data?.online || 0;

    const u = await API('/api/user/page?size=5');
    users.value = u?.data?.records || [];
    stats.value.users = u?.data?.total || 0;
  } catch { /* ignore */ }
  loading.value = false;
  loadBg();
});
</script>