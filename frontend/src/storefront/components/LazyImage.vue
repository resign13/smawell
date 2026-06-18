<template>
  <div
    ref="rootRef"
    :class="['lazy-image-frame', wrapperClass, { 'is-loaded': isLoaded }]"
    :style="frameStyle"
  >
    <div v-if="showSkeleton" class="image-skeleton"></div>
    <img
      v-if="shouldRender"
      :src="src"
      :alt="alt"
      :class="['lazy-image', imgClass, { 'is-loaded': isLoaded }]"
      :style="imgStyle"
      :loading="eager ? 'eager' : 'lazy'"
      :decoding="eager ? 'sync' : 'async'"
      @load="handleLoad"
      @error="handleLoad"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true,
  },
  alt: {
    type: String,
    default: '',
  },
  wrapperClass: {
    type: [String, Array, Object],
    default: '',
  },
  imgClass: {
    type: [String, Array, Object],
    default: '',
  },
  aspectRatio: {
    type: String,
    default: '',
  },
  eager: {
    type: Boolean,
    default: false,
  },
  fit: {
    type: String,
    default: '',
  },
  naturalHeight: {
    type: Boolean,
    default: false,
  },
})

const rootRef = ref(null)
const shouldRender = ref(props.eager)
const isLoaded = ref(false)
let observer = null

const frameStyle = computed(() => (props.aspectRatio ? { aspectRatio: props.aspectRatio } : undefined))
const imgStyle = computed(() => ({
  objectFit: props.fit || undefined,
  height: props.naturalHeight ? 'auto' : undefined,
}))
const showSkeleton = computed(() => !isLoaded.value)

function handleLoad() {
  isLoaded.value = true
}

function cleanupObserver() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

function setupObserver() {
  cleanupObserver()
  if (props.eager || shouldRender.value || typeof window === 'undefined') {
    shouldRender.value = true
    return
  }

  if (!('IntersectionObserver' in window)) {
    shouldRender.value = true
    return
  }

  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        shouldRender.value = true
        cleanupObserver()
      }
    },
    { rootMargin: '220px 0px' }
  )

  if (rootRef.value) {
    observer.observe(rootRef.value)
  }
}

watch(
  () => props.src,
  () => {
    isLoaded.value = false
    shouldRender.value = props.eager
    setupObserver()
  }
)

onMounted(() => {
  setupObserver()
})

onBeforeUnmount(() => {
  cleanupObserver()
})
</script>
