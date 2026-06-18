<template>
  <section class="container order-layout">
    <div class="panel-card">
      <h1>{{ locale.t('order.title') }}</h1>
      <form class="order-form" @submit.prevent="handleSubmit">
        <select v-model.number="form.productId" class="field">
          <option v-for="product in catalog.products" :key="product.id" :value="product.id">
            {{ product.name }} · {{ product.stock }}
          </option>
        </select>
        <input v-model.trim="form.contactName" class="field" :placeholder="locale.t('order.contact')" />
        <input v-model.trim="form.phone" class="field" :placeholder="locale.t('order.phone')" />
        <input v-model.trim="form.country" class="field" :placeholder="locale.t('order.country')" />
        <input v-model.trim="form.shippingAddress" class="field" :placeholder="locale.t('order.address')" />
        <input v-model.number="form.quantity" class="field" type="number" min="1" :placeholder="locale.t('order.quantity')" />
        <textarea v-model.trim="form.note" class="field textarea" :placeholder="locale.t('order.note')"></textarea>
        <button class="primary-button" :disabled="catalog.orderSubmitting" type="submit">{{ locale.t('order.submit') }}</button>
      </form>
      <p v-if="catalog.error" class="error-text">{{ catalog.error }}</p>
      <p v-if="catalog.orderSuccessMessage" class="success-text">{{ catalog.orderSuccessMessage }}</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const route = useRoute()
const auth = useAuthStore()
const catalog = useCatalogStore()
const locale = useLocaleStore()

const form = reactive({
  productId: 0,
  contactName: '',
  phone: '',
  country: '',
  shippingAddress: '',
  quantity: 1,
  note: '',
})

async function handleSubmit() {
  await catalog.createOrder(form)
}

onMounted(async () => {
  if (!catalog.products.length) {
    await catalog.loadProducts({}, locale.current)
  }
  await catalog.loadMyOrders()
  form.contactName = auth.user?.name || ''
  form.productId = Number(route.query.productId) || catalog.products[0]?.id || 0
})
</script>
