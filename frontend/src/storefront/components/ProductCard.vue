<template>
  <article class="product-card">
    <RouterLink :to="`/product/${product.slug}`" class="product-card-media">
      <LazyImage
        :src="product.image"
        :alt="product.name"
        img-class="product-image"
        aspect-ratio="4 / 5.2"
      />
    </RouterLink>

    <div class="product-card-copy">
      <h3>{{ product.name }}</h3>
      <div class="product-price-row">
        <strong>{{ product.formattedPrice }}</strong>
      </div>
      <p class="product-stock-line">{{ locale.t('common.inventory') }} {{ product.stock }}</p>
    </div>
  </article>
</template>

<script setup>
import { RouterLink } from 'vue-router'

import LazyImage from './LazyImage.vue'
import { useLocaleStore } from '../stores/locale'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  showBadge: {
    type: Boolean,
    default: false,
  },
})

const locale = useLocaleStore()
</script>
