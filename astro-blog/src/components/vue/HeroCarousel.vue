<template>
  <div class="relative w-full h-[320px] sm:h-[400px] rounded-2xl overflow-hidden shadow-xl group">
    <!-- Slides -->
    <TransitionGroup name="slide">
      <div
        v-for="item in visible"
        :key="item.slug"
        class="absolute inset-0 cursor-pointer"
        @click="goTo(item.slug)"
      >
        <img
          :src="item.coverImage || `https://picsum.photos/seed/${item.slug}/800/400`"
        @error="(e) => { (e.target as HTMLImageElement).src = `https://picsum.photos/seed/${item.slug}2/800/400` }"
          :alt="item.title"
          class="w-full h-full object-cover"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
        <div class="absolute bottom-0 left-0 right-0 p-8">
          <span v-if="item.categoryName" class="inline-block text-xs px-2.5 py-1 rounded-full bg-white/20 text-white backdrop-blur-sm mb-3">
            {{ item.categoryName }}
          </span>
          <h2 class="text-2xl sm:text-3xl font-bold text-white leading-tight drop-shadow-lg">
            {{ item.title }}
          </h2>
        </div>
      </div>
    </TransitionGroup>

    <!-- Indicators -->
    <div class="absolute bottom-4 right-4 flex gap-1.5 z-10">
      <button
        v-for="(item, i) in articles"
        :key="item.slug"
        @click.stop="goToSlide(i)"
        class="w-2.5 h-2.5 rounded-full transition-all duration-300"
        :class="i === current ? 'bg-white scale-110' : 'bg-white/40 hover:bg-white/70'"
      />
    </div>

    <!-- Arrows -->
    <button
      @click.stop="prev"
      class="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/15 backdrop-blur-sm text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/30"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
    </button>
    <button
      @click.stop="next"
      class="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/15 backdrop-blur-sm text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/30"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

interface Slide {
  slug: string;
  title: string;
  coverImage?: string;
  categoryName?: string;
}

const props = defineProps<{ articles: Slide[] }>();

const current = ref(0);
const visible = computed(() => [props.articles[current.value]]);
let timer: ReturnType<typeof setInterval>;

onMounted(() => {
  if (props.articles.length > 1) {
    timer = setInterval(() => { current.value = (current.value + 1) % props.articles.length; }, 4000);
  }
});
onUnmounted(() => clearInterval(timer));

function goTo(slug: string) { window.location.href = `/blog/${slug}`; }
function goToSlide(i: number) { current.value = i; }
function prev() { current.value = (current.value - 1 + props.articles.length) % props.articles.length; }
function next() { current.value = (current.value + 1) % props.articles.length; }
</script>

<style scoped>
.slide-enter-active { transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-leave-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); position: absolute; }
.slide-enter-from { opacity: 0; transform: scale(1.05); }
.slide-leave-to { opacity: 0; }
</style>
