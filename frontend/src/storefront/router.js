import { createRouter, createWebHistory } from 'vue-router'

import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import AccountView from './views/AccountView.vue'
import OrdersCenterView from './views/OrdersCenterView.vue'
import CheckoutView from './views/CheckoutView.vue'
import ProductDetailView from './views/ProductDetailView.vue'
import ShopView from './views/ShopView.vue'
import InventoryView from './views/InventoryView.vue'
import { pinia } from './stores'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }

    if (to.hash) {
      return {
        el: to.hash,
        top: 104,
        behavior: 'smooth',
      }
    }

    return { top: 0, behavior: 'smooth' }
  },
  routes: [
    { path: '/', component: LoginView, meta: { guestOnly: true } },
    { path: '/login', component: LoginView, meta: { guestOnly: true } },
    { path: '/home', component: HomeView, meta: { requiresAuth: true } },
    { path: '/shop', component: ShopView, meta: { requiresAuth: true } },
    { path: '/inventory', component: InventoryView, meta: { requiresAuth: true } },
    { path: '/collections/:sectionSlug', component: ShopView, meta: { requiresAuth: true } },
    { path: '/product/:slug', component: ProductDetailView, meta: { requiresAuth: true } },
    { path: '/checkout', component: CheckoutView, meta: { requiresAuth: true } },
    { path: '/account', component: AccountView, meta: { requiresAuth: true } },
    { path: '/orders', component: OrdersCenterView, meta: { requiresAuth: true } },
    { path: '/order', redirect: '/orders' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore(pinia)
  if (!auth.initialized) {
    await auth.initialize()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: '1' } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return '/home'
  }

  return true
})

export default router
