<template>
  <div class="fixed inset-0 pointer-events-none z-50 overflow-hidden">
    <span
      v-for="p in petals"
      :key="p.id"
      class="petal"
      :style="p.style"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Petal {
  id: number;
  style: Record<string, string>;
}

const petals = ref<Petal[]>([]);

onMounted(() => {
  const items: Petal[] = [];
  for (let i = 0; i < 50; i++) {
    const size = 4 + Math.random() * 5;
    const left = Math.random() * 100;
    const delay = Math.random() * 12;
    const duration = 8 + Math.random() * 10;
    const drift = -20 + Math.random() * 40;
    const opacity = 0.3 + Math.random() * 0.5;

    items.push({
      id: i,
      style: {
        left: `${left}%`,
        width: `${size}px`,
        height: `${size * 1.3}px`,
        opacity: `${opacity}`,
        animationDuration: `${duration}s`,
        animationDelay: `${delay}s`,
        '--drift': `${drift}px`,
      },
    });
  }
  petals.value = items;
});
</script>

<style scoped>
.petal {
  position: absolute;
  top: -20px;
  background: linear-gradient(180deg, #f8b4c8 0%, #f4729e 50%, #f8b4c8 100%);
  border-radius: 50% 0 50% 0;
  animation: fall linear infinite;
  transform: rotate(0deg);
}

@keyframes fall {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg);
    opacity: 1;
  }
  25% {
    transform: translateY(25vh) translateX(var(--drift)) rotate(90deg);
  }
  50% {
    transform: translateY(50vh) translateX(calc(var(--drift) * -0.5)) rotate(180deg);
    opacity: 0.8;
  }
  75% {
    transform: translateY(75vh) translateX(calc(var(--drift) * 1.2)) rotate(270deg);
  }
  100% {
    transform: translateY(105vh) translateX(calc(var(--drift) * -0.3)) rotate(360deg);
    opacity: 0.2;
  }
}
</style>