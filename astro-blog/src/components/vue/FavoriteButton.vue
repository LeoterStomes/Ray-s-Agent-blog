<template>
  <button
    @click="toggle"
    :disabled="loading"
    class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-button text-sm transition-all"
    :class="favorited ? 'text-red-500 bg-red-50 hover:bg-red-100' : 'text-gray-400 hover:text-red-400 hover:bg-red-50'"
  >
    <svg class="w-4 h-4" :fill="favorited ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
    <span>{{ count }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { $isLoggedIn, openAuth } from '@lib/store';
import { request } from '@lib/api';
import { API } from '@lib/constants';

const props = defineProps<{
  articleId: string;
  initialFavorited?: boolean;
  initialCount?: number;
}>();

const favorited = ref(props.initialFavorited || false);
const count = ref(props.initialCount || 0);
const loading = ref(false);

async function toggle() {
  if (!$isLoggedIn.get()) {
    openAuth('login');
    return;
  }

  loading.value = true;
  try {
    if (favorited.value) {
      await request(API.ENDPOINTS.FAVORITE_TOGGLE(props.articleId), { method: 'DELETE' });
      favorited.value = false;
      count.value = Math.max(0, count.value - 1);
    } else {
      await request(API.ENDPOINTS.FAVORITE_TOGGLE(props.articleId), { method: 'POST' });
      favorited.value = true;
      count.value = count.value + 1;
    }
  } catch (e: any) {
    // silently fail
  } finally {
    loading.value = false;
  }
}
</script>
