<template>
  <div v-if="!ready" class="admin-loading">验证权限中...</div>
  <slot v-else-if="ok" />
  <div v-else class="admin-denied">
    <p>无权访问管理后台</p>
    <a href="/login">去登录</a>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getUserType, isLoggedIn } from '@lib/auth';

const ready = ref(false);
const ok = ref(false);

onMounted(() => {
  if (isLoggedIn() && getUserType(JSON.parse(localStorage.getItem('userInfo') || '{}')) === 2) {
    ok.value = true;
  } else {
    // 未登录或非管理员 → 跳转登录
    window.location.href = '/login';
  }
  ready.value = true;
});
</script>

<style scoped>
.admin-loading, .admin-denied { text-align: center; padding: 60px 20px; }
.admin-denied a { color: #5b7bff; }
</style>
