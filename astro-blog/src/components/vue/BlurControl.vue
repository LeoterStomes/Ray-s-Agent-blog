<template>
  <!-- Toggle button -->
  <button
    @click="open = !open"
    class="fixed top-36 right-6 z-30 w-9 h-9 rounded-full glass-card flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors shadow-sm"
    title="面板透明度"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
  </button>

  <!-- Control panel -->
  <Transition name="panel">
    <div v-if="open" class="fixed top-36 right-14 z-30 w-60 glass-card p-4 shadow-xl">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide">面板透明度</h3>
        <button @click="open = false" class="text-gray-300 hover:text-gray-500">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="space-y-4">
        <!-- Opacity -->
        <div>
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>不透明度</span>
            <span>{{ Math.round(opacity * 100) }}%</span>
          </div>
          <input
            v-model.number="opacity"
            type="range" min="0.1" max="1" step="0.05"
            class="w-full h-1.5 rounded-full appearance-none bg-gray-200 cursor-pointer accent-brand-600"
          />
        </div>

        <!-- Blur -->
        <div>
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>模糊度</span>
            <span>{{ Math.round(blur) }}px</span>
          </div>
          <input
            v-model.number="blur"
            type="range" min="0" max="30" step="1"
            class="w-full h-1.5 rounded-full appearance-none bg-gray-200 cursor-pointer accent-brand-600"
          />
        </div>

        <div class="flex gap-2">
          <button
            v-for="preset in presets"
            :key="preset.label"
            @click="apply(preset.o, preset.b)"
            class="flex-1 text-xs py-1 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
          >
            {{ preset.label }}
          </button>
        </div>

        <hr class="border-gray-100" />

        <!-- Dark mode -->
        <div>
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>深夜模式</span>
            <span>{{ dark ? '开' : '关' }}</span>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="dark" type="checkbox" class="hidden" @change="toggleDark" />
            <div class="w-9 h-5 rounded-full transition-colors" :class="dark ? 'bg-brand-600' : 'bg-gray-300'">
              <div class="w-4 h-4 rounded-full bg-white shadow mt-0.5 transition-transform" :class="dark ? 'translate-x-4' : 'translate-x-0.5'" />
            </div>
            <span class="text-xs text-gray-400">{{ dark ? '暗色背景' : '亮色背景' }}</span>
          </label>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';

const open = ref(false);
const opacity = ref(0.75);
const blur = ref(12);
const dark = ref(false);

function toggleDark() {
  if (dark.value) {
    document.documentElement.classList.add('dark-mode');
  } else {
    document.documentElement.classList.remove('dark-mode');
  }
  localStorage.setItem('dark-mode', String(dark.value));
}

const presets = [
  { label: '透亮', o: 0.4, b: 4 },
  { label: '默认', o: 0.75, b: 12 },
  { label: '磨砂', o: 0.9, b: 24 },
];

onMounted(() => {
  const saved = localStorage.getItem('panel-style');
  if (saved) {
    try {
      const s = JSON.parse(saved);
      opacity.value = s.opacity;
      blur.value = s.blur;
    } catch { /* ignore */ }
  }
  apply(opacity.value, blur.value);
  // Restore dark mode
  if (localStorage.getItem('dark-mode') === 'true') {
    dark.value = true;
    document.documentElement.classList.add('dark-mode');
  }
});

watch([opacity, blur], () => {
  apply(opacity.value, blur.value);
  localStorage.setItem('panel-style', JSON.stringify({ opacity: opacity.value, blur: blur.value }));
});

function apply(o: number, b: number) {
  document.documentElement.style.setProperty('--panel-opacity', String(o));
  document.documentElement.style.setProperty('--panel-blur', b + 'px');
}
</script>

<style scoped>
.panel-enter-active { transition: all 0.2s ease; }
.panel-leave-active { transition: all 0.15s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateX(8px); }
</style>
