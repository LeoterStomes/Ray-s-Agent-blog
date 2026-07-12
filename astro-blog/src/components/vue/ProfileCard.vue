<template>
  <div class="glass-card p-4 text-center">
    <!-- 已登录：显示用户信息 -->
    <template v-if="loggedIn && user">
      <div class="avatar-ring-wrapper">
        <div class="avatar-ring" />
        <!-- 兜底 DiceBear 始终在最底层 -->
        <img
          :src="fallbackAvatar"
          alt=""
          class="avatar-img avatar-fallback"
        />
        <!-- 真实头像叠在上层，加载成功则覆盖兜底 -->
        <img
          v-if="realAvatarUrl"
          :src="realAvatarUrl"
          alt="avatar"
          class="avatar-img avatar-real"
          :class="{ loaded: imgLoaded }"
          @load="imgLoaded = true"
          @error="imgLoaded = false"
        />
      </div>
      <h3 class="text-sm font-bold text-gray-700 mt-3">{{ user.nickname || user.username }}</h3>
      <p class="text-xs text-gray-400 mt-1 mb-4">{{ user.bio || '这个用户很懒，什么都没写~' }}</p>
    </template>

    <!-- 未登录：引导登录 -->
    <template v-else>
      <div class="avatar-ring-wrapper cursor-pointer" @click="goLogin">
        <div class="avatar-ring ring-paused" />
        <div class="avatar-placeholder">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      </div>
      <h3 class="text-sm font-bold text-gray-500 mt-3 cursor-pointer hover:text-brand-600 transition-colors" @click="goLogin">
        请登录
      </h3>
      <p class="text-xs text-gray-400 mt-1 mb-4">登录后展示个人资料</p>
    </template>

    <!-- 社交链接 -->
    <div class="flex items-center justify-center gap-3">
      <a
        v-for="link in links"
        :key="link.label"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
        :title="link.label"
        class="w-8 h-8 rounded-full flex items-center justify-center transition-all hover:scale-110 hover:shadow-lg"
        :style="{ backgroundColor: link.bgColor, color: '#fff' }"
      >
        <span v-html="link.icon" class="w-4 h-4 flex items-center justify-center" />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { $isLoggedIn, $currentUser, $avatarUrl } from '@lib/store';
import type { UserInfo } from '@lib/auth';

const loggedIn = ref(false);
const user = ref<UserInfo | null>(null);
const avatarFromStore = ref('');
const imgLoaded = ref(false);

/** 兜底头像：始终使用 DiceBear，真实头像加载成功后覆盖在上面 */
const fallbackAvatar = computed(() => {
  const seed = user.value?.nickname || user.value?.username || 'User';
  return `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(seed)}&backgroundColor=5b7bff`;
});

/** 真实头像 URL（可能无效），若为空字符串则不渲染该 img */
const realAvatarUrl = computed(() => {
  if (!avatarFromStore.value) return '';
  return avatarFromStore.value;
});

let unsubLoggedIn: (() => void) | null = null;
let unsubUser: (() => void) | null = null;
let unsubAvatar: (() => void) | null = null;

onMounted(() => {
  loggedIn.value = $isLoggedIn.get();
  user.value = $currentUser.get();
  avatarFromStore.value = $avatarUrl.get();

  unsubLoggedIn = $isLoggedIn.listen((v) => { loggedIn.value = v; });
  unsubUser = $currentUser.listen((u) => { user.value = u; });
  unsubAvatar = $avatarUrl.listen((v) => {
    avatarFromStore.value = v;
    imgLoaded.value = false;  // 头像变更时重置加载状态
  });
});

onUnmounted(() => {
  unsubLoggedIn?.();
  unsubUser?.();
  unsubAvatar?.();
});

function goLogin() {
  window.location.href = '/auth/login';
}

const links = [
  {
    label: 'GitHub',
    url: 'https://github.com',
    bgColor: '#24292e',
    icon: '<svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>',
  },
  {
    label: 'Bilibili',
    url: 'https://space.bilibili.com',
    bgColor: '#fb7299',
    icon: '<svg fill="currentColor" viewBox="0 0 24 24"><path d="M17.813 4.653h.854c1.51.054 2.769.578 3.773 1.574 1.004.995 1.524 2.249 1.56 3.76v7.36c-.036 1.51-.556 2.769-1.56 3.773s-2.262 1.524-3.773 1.56H5.333c-1.51-.036-2.769-.556-3.773-1.56S.036 19.858 0 18.347v-7.36c.036-1.511.556-2.765 1.56-3.76 1.004-.996 2.262-1.52 3.773-1.574h.774l-1.174-1.12a1.234 1.234 0 01-.373-.906c0-.356.124-.659.373-.907l.027-.027c.267-.249.573-.373.92-.373.347 0 .653.124.92.373L9.653 4.44c.071.071.134.142.187.213h4.267a.836.836 0 01.16-.213l2.853-2.747c.267-.249.573-.373.92-.373.347 0 .662.151.929.4.267.249.391.551.391.907 0 .355-.124.657-.373.906zM5.333 7.24c-.746.018-1.373.276-1.88.773-.506.498-.769 1.13-.786 1.894v7.52c.017.764.28 1.395.786 1.893.507.498 1.134.756 1.88.773h13.334c.746-.017 1.373-.275 1.88-.773.506-.498.769-1.129.786-1.893v-7.52c-.017-.765-.28-1.396-.786-1.894-.507-.497-1.134-.755-1.88-.773zM8 11.107c.373 0 .684.124.933.373.25.249.383.569.4.96v1.173c-.017.391-.15.711-.4.96-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.383-.569-.4-.96V12.44c0-.373.129-.689.386-.947.258-.257.574-.386.947-.386zm8 0c.373 0 .684.124.933.373.25.249.383.569.4.96v1.173c-.017.391-.15.711-.4.96-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.383-.569-.4-.96V12.44c.017-.391.15-.711.4-.96.249-.249.56-.373.933-.373z"/></svg>',
  },
  {
    label: 'Email',
    url: 'mailto:ray@blog.com',
    bgColor: '#5b7bff',
    icon: '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>',
  },
];
</script>

<style scoped>
/* ── Avatar ring ── */
.avatar-ring-wrapper {
  position: relative;
  width: 5rem;
  height: 5rem;
  margin: 0 auto;
}
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  padding: 3px;
  background: white;
}
/* 兜底 DiceBear 始终在底层 */
.avatar-fallback {
  position: relative;
  z-index: 1;
}
/* 真实头像叠在上层，加载成功后覆盖兜底 */
.avatar-real {
  position: absolute;
  inset: 0;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.3s;
}
.avatar-real.loaded {
  opacity: 1;
}
.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  position: relative;
  z-index: 1;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #5b7bff, #a855f7, #ec4899, #f59e0b, #22c55e, #5b7bff);
  animation: ring-spin 3s linear infinite;
  z-index: 0;
}
.ring-paused {
  animation-play-state: paused;
  opacity: 0.5;
}
@keyframes ring-spin {
  to { transform: rotate(360deg); }
}
</style>