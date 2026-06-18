<template>
  <section class="login-page simple-login-page">
    <div class="container simple-login-layout">
      <aside class="simple-brand-card">
        <p class="eyebrow">{{ locale.t('brand.name') }}</p>
        <h1>{{ loginCopy.brandTitle }}</h1>
        <p>{{ loginCopy.brandText }}</p>
        <div class="simple-brand-pills">
          <span v-for="item in loginCopy.brandPills" :key="item">{{ item }}</span>
        </div>
      </aside>

      <div class="simple-login-card">
        <p class="eyebrow">{{ loginCopy.overline }}</p>
        <h2>{{ loginCopy.title }}</h2>
        <p class="login-form-text">{{ loginCopy.text }}</p>
        <p v-if="route.query.redirect" class="login-notice">{{ loginCopy.protectedNotice }}</p>

        <form class="login-form" @submit.prevent="handleLogin">
          <input v-model.trim="form.email" :placeholder="loginCopy.email" class="field" />
          <input v-model.trim="form.password" type="password" :placeholder="loginCopy.password" class="field" />
          <button class="primary-button" :disabled="auth.loading" type="submit">
            {{ loginCopy.submit }}
          </button>
        </form>

        <p v-if="auth.error" class="error-text">{{ auth.error }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const auth = useAuthStore()
const catalog = useCatalogStore()
const locale = useLocaleStore()
const route = useRoute()
const router = useRouter()

const loginCopy = computed(() => ({
  overline: 'BUYER ACCESS',
  title: 'SMAWELL Buyer Login',
  text: 'Sign in to view the homepage, category browsing, product detail, cart and checkout.',
  protectedNotice: 'This page is available after login.',
  email: 'Email',
  password: 'Password',
  submit: 'Login to Continue',
  brandTitle: 'A premium apparel storefront for womenswear and menswear',
  brandText: 'SMAWELL now presents womenswear, menswear, pants, denim and outerwear with a cleaner homepage, richer media and a cart-based checkout flow.',
  brandPills: ['Womenswear', 'Menswear', 'Cart checkout'],
}))

const form = reactive({
  email: '',
  password: '',
})

async function handleLogin() {
  const ok = await auth.login(form)
  if (!ok) return
  catalog.primeHomeLoading()
  await router.replace('/home')
}
</script>
