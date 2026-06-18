<template>
  <div class="app-shell">
    <SiteHeader />
    <main class="page-shell">
      <RouterView />
    </main>
    <SiteFooter v-if="!isLoginRoute" />
  </div>
</template>

<script setup>
import { computed, watchEffect } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import SiteFooter from './components/SiteFooter.vue'
import SiteHeader from './components/SiteHeader.vue'
import { useLocaleStore } from './stores/locale'

const locale = useLocaleStore()
const route = useRoute()
const isLoginRoute = computed(() => route.path === '/' || route.path === '/login')

watchEffect(() => {
  document.documentElement.lang = locale.current
})
</script>
