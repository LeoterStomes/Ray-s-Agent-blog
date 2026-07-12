<template>
  <span ref="eyeRef" class="eyeball" :style="{ width: size + 'px', height: isBlinking ? '2px' : size + 'px', marginTop: isBlinking ? (size / 2) + 'px' : '0' }">
    <span v-if="!isBlinking" class="pupil" :style="{ width: pupilSize + 'px', height: pupilSize + 'px', backgroundColor: pupilColor, borderRadius: '50%', transform: `translate(${tx}px, ${ty}px)`, transition: 'transform 0.1s ease-out' }" />
  </span>
</template>

<script setup lang="ts">
import { watchEffect, ref } from 'vue';

const props = withDefaults(defineProps<{
  size?: number;
  pupilSize?: number;
  isBlinking?: boolean;
  mouseX?: number;
  mouseY?: number;
  forceLookX?: number;
  forceLookY?: number;
  pupilColor?: string;
  maxDistance?: number;
}>(), {
  size: 18,
  pupilSize: 7,
  isBlinking: false,
  mouseX: 0,
  mouseY: 0,
  pupilColor: '#2D2D2D',
  maxDistance: 5,
});

const eyeRef = ref<HTMLElement>();
const tx = ref(0);
const ty = ref(0);

watchEffect(() => {
  const fx = props.forceLookX;
  const fy = props.forceLookY;
  if (fx !== undefined && fy !== undefined) {
    tx.value = fx;
    ty.value = fy;
    return;
  }
  if (!eyeRef.value) return;
  const rect = eyeRef.value.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const dx = props.mouseX - cx;
  const dy = props.mouseY - cy;
  const dist = Math.min(Math.sqrt(dx * dx + dy * dy), props.maxDistance);
  const angle = Math.atan2(dy, dx);
  tx.value = Math.cos(angle) * dist;
  ty.value = Math.sin(angle) * dist;
});
</script>

<style scoped>
.eyeball {
  border-radius: 50%;
  background: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: height 0.15s ease, margin-top 0.15s ease;
}
.pupil {
  border-radius: 50%;
  transition: transform 0.1s ease-out;
}
</style>