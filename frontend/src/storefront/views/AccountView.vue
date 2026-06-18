<template>
  <section class="account-page">
    <div class="container account-layout">
      <article class="panel-card account-profile-card">
        <p class="eyebrow">{{ copy.overline }}</p>
        <h1>{{ copy.title }}</h1>
        <p class="helper">{{ copy.subtitle }}</p>

        <div class="account-profile-grid">
          <div>
            <span>{{ copy.buyer }}</span>
            <strong>{{ auth.user?.name || '--' }}</strong>
          </div>
          <div>
            <span>{{ copy.company }}</span>
            <strong>{{ auth.user?.companyName || '--' }}</strong>
          </div>
          <div>
            <span>{{ copy.email }}</span>
            <strong>{{ auth.user?.email || '--' }}</strong>
          </div>
          <div>
            <span>{{ copy.status }}</span>
            <strong>{{ auth.user?.status || copy.active }}</strong>
          </div>
        </div>
      </article>

      <article class="panel-card account-shortcuts-card">
        <div class="account-shortcuts-head">
          <div>
            <p class="eyebrow">{{ copy.quickOverline }}</p>
            <h2>{{ copy.quickTitle }}</h2>
            <p class="helper">{{ copy.quickText }}</p>
          </div>
        </div>

        <div class="account-shortcuts-grid">
          <RouterLink class="account-shortcut-item" to="/orders">
            <strong>{{ copy.ordersTitle }}</strong>
            <span>{{ copy.ordersText }}</span>
          </RouterLink>

          <RouterLink class="account-shortcut-item" to="/shop">
            <strong>{{ copy.shopTitle }}</strong>
            <span>{{ copy.shopText }}</span>
          </RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useLocaleStore } from '../stores/locale'

const auth = useAuthStore()
const locale = useLocaleStore()

const copy = computed(() => ({
  overline: 'BUYER CENTER',
  title: 'User Center',
  subtitle: 'Review the current buyer account and jump into orders or product browsing.',
  buyer: 'Buyer',
  company: 'Company',
  email: 'Email',
  status: 'Status',
  active: 'Active',
  quickOverline: 'QUICK ACCESS',
  quickTitle: 'Quick Access',
  quickText: 'Account details and order management now live on separate pages.',
  ordersTitle: 'Order Center',
  ordersText: 'View orders, filter by status, pay pending orders and cancel them before shipment.',
  shopTitle: 'Continue Shopping',
  shopText: 'Go back to the storefront and keep browsing products.',
}))
</script>
