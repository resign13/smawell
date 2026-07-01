<template>
  <header class="site-header">
    <div class="container header-inner">
      <RouterLink class="brand brand-wordmark" to="/home">
        {{ locale.t('brand.name') }}
      </RouterLink>

      <nav class="nav-links">
        <div class="nav-dropdown">
          <RouterLink class="nav-link-button" to="/shop">{{ navCopy.shop }}</RouterLink>
          <div class="nav-dropdown-panel">
            <div class="nav-dropdown-columns">
              <div
                v-for="section in dropdownSections"
                :key="section.title"
                class="nav-dropdown-group"
              >
                <h3>{{ section.title }}</h3>
                <RouterLink
                  v-for="item in section.items"
                  :key="`${section.title}-${item.label}`"
                  class="nav-dropdown-item"
                  :to="item.to"
                >
                  {{ item.label }}
                </RouterLink>
              </div>
            </div>
            <div class="nav-dropdown-footer">
              <RouterLink class="nav-dropdown-all-link" to="/shop">
                {{ navCopy.viewAll }}
              </RouterLink>
              <span>{{ navCopy.dropdownText }}</span>
            </div>
          </div>
        </div>

        <RouterLink class="nav-link-button" to="/collections/best-seller">
          {{ navCopy.bestSeller }}
        </RouterLink>
        <RouterLink class="nav-link-button" to="/collections/new-arrival">
          {{ navCopy.newArrival }}
        </RouterLink>
        <RouterLink class="nav-link-button" to="/collections/special-price">
          {{ navCopy.preOrder }}
        </RouterLink>
        <RouterLink class="nav-link-button" to="/inventory">
          {{ navCopy.inventory }}
        </RouterLink>
        <RouterLink class="nav-link-button" :to="{ path: '/home', hash: '#about' }">
          {{ navCopy.about }}
        </RouterLink>
        <a class="nav-link-button" href="/home#contact">{{ navCopy.contact }}</a>
      </nav>
      <div class="header-actions">
        <RouterLink v-if="!auth.isAuthenticated" class="text-action" to="/login">
          {{ navCopy.login }}
        </RouterLink>

        <template v-else>
          <button class="text-action" type="button" @click="handleLogout">
            {{ navCopy.logout }}
          </button>

          <button class="icon-link" type="button" :title="navCopy.search">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10.5 4a6.5 6.5 0 1 0 4.094 11.55l4.428 4.428 1.414-1.414-4.428-4.428A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" />
            </svg>
          </button>

          <RouterLink class="icon-link" to="/account" :title="navCopy.account">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 12a4.5 4.5 0 1 0-4.5-4.5A4.5 4.5 0 0 0 12 12Zm0 2c-4 0-7 2-7 4.8V21h14v-2.2C19 16 16 14 12 14Z" />
            </svg>
          </RouterLink>
          <RouterLink class="icon-link" to="/orders" :title="navCopy.orders">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 4h14v16H5V4Zm2 3v2h10V7H7Zm0 4v2h10v-2H7Zm0 4v2h6v-2H7Z" />
            </svg>
          </RouterLink>

          <RouterLink class="icon-link cart-link" to="/checkout" :title="navCopy.checkout">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M7 6h14l-1.5 8.5H9L7 6Zm-2-2H2v2h2l1.8 9.6A2.5 2.5 0 0 0 8.3 18h10.9v-2H8.6a.5.5 0 0 1-.5-.4L7.8 14h12.3A2 2 0 0 0 22 12.3L23.7 4H5Zm4 17a1.5 1.5 0 1 0 1.5-1.5A1.5 1.5 0 0 0 9 21Zm8 0a1.5 1.5 0 1 0 1.5-1.5A1.5 1.5 0 0 0 17 21Z" />
            </svg>
            <span v-if="cart.itemCount" class="cart-badge">{{ cart.itemCount }}</span>
          </RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'
import { useLocaleStore } from '../stores/locale'
import { useCatalogStore } from '../stores/catalog'

const auth = useAuthStore()
const cart = useCartStore()
const locale = useLocaleStore()
const catalog = useCatalogStore()

const navCopy = {
  dropdownText: 'Explore the full SMAWELL catalog by category.',
  shop: 'SHOP',
  bestSeller: 'BEST SELLER',
  newArrival: 'NEW ARRIVAL',
  preOrder: 'PRE-ORDER',
  inventory: 'INVENTORY',
  about: 'ABOUT',
  contact: 'CONTACT',
  viewAll: 'VIEW ALL PRODUCTS',
  login: 'Sign In',
  logout: 'Logout',
  search: 'Search',
  account: 'Account',
  orders: 'Orders',
  checkout: 'Cart',
}

const dropdownSections = computed(() => [
  {
    title: 'CATEGORIES',
    items: (catalog.categories || []).map((item) => ({
      label: item.label || item.key,
      to: `/shop${item.key ? `?category=${item.key}` : ''}`,
    })),
  },
])

async function ensureCategoriesLoaded() {
  if ((catalog.categories || []).length) return
  await catalog.loadHome('en')
}

onMounted(() => {
  ensureCategoriesLoaded()
})

async function handleLogout() {
  await auth.logout()
  cart.clear()
  window.location.replace('/login')
}
</script>
