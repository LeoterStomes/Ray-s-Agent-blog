<template>
  <div>
    <!-- Not logged in -->
    <div v-if="!loggedIn" class="text-center py-16 glass-card">
      <p class="text-gray-400 text-lg mb-4">请先登录</p>
      <a href="/auth/login" class="px-6 py-2.5 rounded-button bg-brand-600 text-white font-medium hover:bg-brand-700 transition-colors inline-block no-underline">
        去登录
      </a>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="text-center py-16 glass-card">
      <p class="text-gray-400">加载中...</p>
    </div>

    <div v-else class="space-y-6">
      <!-- Profile Form -->
      <div class="glass-card p-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">基本资料</h2>
        <div v-if="successMsg" class="mb-4 p-3 rounded-lg bg-green-50 text-green-600 text-sm">{{ successMsg }}</div>
        <div v-if="errorMsg" class="mb-4 p-3 rounded-lg bg-red-50 text-red-600 text-sm">{{ errorMsg }}</div>

        <!-- Avatar -->
        <div class="flex items-center gap-4 mb-6">
          <img
            :src="avatarPreview"
            class="w-16 h-16 rounded-full object-cover ring-2 ring-brand-100"
            @error="(e) => { (e.target as HTMLImageElement).src = 'https://api.dicebear.com/7.x/initials/svg?seed=' + (user?.username || 'U') + '&backgroundColor=5b7bff' }"
          />
          <label class="px-4 py-2 rounded-button border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer">
            更换头像
            <input type="file" accept="image/*" class="hidden" @change="uploadAvatar" />
          </label>
          <span v-if="uploading" class="text-xs text-gray-400">上传中...</span>
        </div>

        <form @submit.prevent="saveProfile" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">用户名</label>
            <input :value="user?.username" disabled class="w-full px-4 py-2.5 border border-gray-200 rounded-button bg-gray-50 text-gray-400 outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">昵称</label>
            <input v-model="profile.nickname" type="text" class="w-full px-4 py-2.5 border border-gray-200 rounded-button focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">邮箱</label>
            <input v-model="profile.email" type="email" class="w-full px-4 py-2.5 border border-gray-200 rounded-button focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">手机号</label>
            <input v-model="profile.phone" type="text" class="w-full px-4 py-2.5 border border-gray-200 rounded-button focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">个性签名</label>
            <input v-model="profile.bio" type="text" maxlength="100" placeholder="介绍一下自己吧" class="w-full px-4 py-2.5 border border-gray-200 rounded-button focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all" />
            <p class="text-xs text-gray-400 mt-1">{{ (profile.bio || '').length }}/100</p>
          </div>
          <button type="submit" :disabled="saving" class="px-6 py-2.5 rounded-button bg-brand-600 text-white font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </form>
      </div>

      <!-- Password Form -->
      <div class="glass-card p-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">修改密码</h2>
        <div v-if="pwdMsg" class="mb-4 p-3 rounded-lg text-sm" :class="pwdOk ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'">{{ pwdMsg }}</div>

        <form @submit.prevent="savePassword" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">新密码</label>
            <input v-model="passwords.newPass" type="password" required class="w-full px-4 py-2.5 border border-gray-200 rounded-button focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">确认新密码</label>
            <input v-model="passwords.confirmPass" type="password" required class="w-full px-4 py-2.5 border border-gray-200 rounded-button focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all" />
          </div>
          <button type="submit" :disabled="savingPwd" class="px-6 py-2.5 rounded-button border border-gray-200 text-gray-600 font-medium hover:bg-gray-50 transition-colors disabled:opacity-50">
            {{ savingPwd ? '修改中...' : '修改密码' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { $isLoggedIn, $currentUser, openAuth, updateUser } from '@lib/store';
import { request } from '@lib/api';
import { API } from '@lib/constants';
import type { UserInfo } from '@lib/auth';

const loggedIn = ref(false);
const loading = ref(true);
const user = ref<UserInfo | null>(null);
const profile = ref({ nickname: '', email: '', phone: '', bio: '' });
const saving = ref(false);
const successMsg = ref('');
const errorMsg = ref('');
const avatarPreview = ref('');
const uploading = ref(false);

const passwords = ref({ newPass: '', confirmPass: '' });
const savingPwd = ref(false);
const pwdMsg = ref('');
const pwdOk = ref(false);

onMounted(async () => {
  loggedIn.value = $isLoggedIn.get();
  if (loggedIn.value) {
    user.value = $currentUser.get();
    try {
      const data = await request<any>(API.ENDPOINTS.CURRENT_USER);
      user.value = data;
      avatarPreview.value = data.avatar || '';
      profile.value = {
        nickname: data.nickname || '',
        email: data.email || '',
        phone: data.phone || '',
        bio: data.bio || '',
      };
    } catch { /* ignore */ }
  }
  loading.value = false;
});

async function uploadAvatar(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token') || '';
    const res = await fetch('/api/file/simple/upload/image', {
      method: 'POST',
      headers: { token },
      body: formData,
    });
    const json = await res.json();
    if (json.code === '200' && json.data?.url) {
      avatarPreview.value = json.data.url;
      if (user.value) {
        user.value.avatar = json.data.url;
        updateUser({ ...user.value });
      }
      successMsg.value = '头像已更新';
    } else {
      errorMsg.value = json.msg || '上传失败';
    }
  } catch {
    errorMsg.value = '上传失败，请重试';
  } finally {
    uploading.value = false;
  }
}

async function saveProfile() {
  saving.value = true;
  errorMsg.value = '';
  successMsg.value = '';
  try {
    const data = await request<any>(API.ENDPOINTS.UPDATE_PROFILE, {
      method: 'PUT',
      body: profile.value,
    });
    user.value = data;
    updateUser({ ...data });
    avatarPreview.value = data.avatar || '';
    successMsg.value = '资料已更新';
  } catch (e: any) {
    errorMsg.value = e.message || '保存失败';
  } finally {
    saving.value = false;
  }
}

async function savePassword() {
  if (passwords.value.newPass !== passwords.value.confirmPass) {
    pwdMsg.value = '两次密码不一致';
    pwdOk.value = false;
    return;
  }
  savingPwd.value = true;
  pwdMsg.value = '';
  try {
    await request(API.ENDPOINTS.UPDATE_PASSWORD, {
      method: 'PUT',
      body: { password: passwords.value.newPass },
    });
    pwdMsg.value = '密码修改成功';
    pwdOk.value = true;
    passwords.value = { newPass: '', confirmPass: '' };
  } catch (e: any) {
    pwdMsg.value = e.message || '修改失败';
    pwdOk.value = false;
  } finally {
    savingPwd.value = false;
  }
}
</script>
