<template>
  <div class="flex items-center gap-3">
    <template v-if="loggedIn">
      <UserMenu />
    </template>
    <template v-else>
      <a href="/auth/login" class="text-sm text-brand-600 hover:text-brand-700 font-medium transition-colors">
        登录
      </a>
      <a
        href="/auth/login?mode=register"
        class="text-sm px-4 py-1.5 rounded-button bg-brand-600 text-white hover:bg-brand-700 transition-colors shadow-sm"
      >
        注册
      </a>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { $isLoggedIn } from '@lib/store';
import UserMenu from './UserMenu.vue';

const loggedIn = ref(false);

onMounted(() => {
  loggedIn.value = $isLoggedIn.get();
  $isLoggedIn.listen((val) => { loggedIn.value = val; });
});
</script>
