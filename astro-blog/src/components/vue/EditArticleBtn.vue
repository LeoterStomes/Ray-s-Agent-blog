<template>
  <a v-if="isAdmin" :href="'/editor?id=' + articleId" class="edit-article-btn" title="编辑文章">
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
    编辑
  </a>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getUserType } from '@lib/auth';

defineProps<{ articleId: string }>();

const isAdmin = ref(false);
onMounted(() => {
  isAdmin.value = getUserType(JSON.parse(localStorage.getItem('userInfo') || '{}')) === 2;
});
</script>

<style scoped>
.edit-article-btn {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 13px; color: #f59e0b; font-weight: 500; text-decoration: none;
  padding: 4px 10px; border: 1px solid #f59e0b30; border-radius: 6px;
  transition: background .15s, color .15s;
}
.edit-article-btn:hover { background: #f59e0b1a; color: #fbbf24; }
</style>