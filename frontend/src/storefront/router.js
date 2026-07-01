import { createRouter, createWebHistory } from 'vue-router'

import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import AccountView from './views/AccountView.vue'
import OrdersCenterView from './views/OrdersCenterView.vue'
import CheckoutView from './views/CheckoutView.vue'
import ProductDetailView from './views/ProductDetailView.vue'
import ShopView from './views/ShopView.vue'
import InventoryView from './views/InventoryView.vue'
import ContentPageView from './views/ContentPageView.vue'
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
    { path: '/', redirect: '/home' },
    { path: '/login', component: LoginView, meta: { guestOnly: true } },
    { path: '/home', component: HomeView },
    { path: '/shop', component: ShopView },
    { path: '/inventory', component: InventoryView },
    { path: '/collections/:sectionSlug', component: ShopView },
    { path: '/product/:slug', component: ProductDetailView },
    { path: '/checkout', component: CheckoutView },
    { path: '/account', component: AccountView },
    { path: '/orders', component: OrdersCenterView },
    { path: '/order', redirect: '/orders' },
    { path: '/pages/:slug', component: ContentPageView },
  ],
})

router.beforeEach(async () => {
  const auth = useAuthStore(pinia)
  if (!auth.initialized) {
    await auth.initialize()
  }

  return true
})

export default router
