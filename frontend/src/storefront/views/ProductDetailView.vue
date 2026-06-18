<template>
  <section class="product-detail-page">
    <div v-if="catalog.detailLoading" class="container product-detail-layout detail-skeleton-layout">
      <div class="product-gallery-column">
        <div class="product-main-image skeleton-media skeleton-media-detail"></div>
        <div class="product-thumb-row">
          <div v-for="item in thumbSkeletons" :key="item" class="product-thumb skeleton-thumb"></div>
        </div>
      </div>

      <div class="product-buy-column detail-copy-skeleton">
        <span class="skeleton-line skeleton-line-xs"></span>
        <span class="skeleton-line skeleton-line-title"></span>
        <span class="skeleton-line skeleton-line-sm"></span>
        <span class="skeleton-line skeleton-line-lg"></span>
        <span class="skeleton-line skeleton-line-md"></span>

        <div class="detail-size-grid">
          <span v-for="item in sizeSkeletons" :key="item" class="skeleton-button skeleton-size-button"></span>
        </div>

        <div class="skeleton-benefits">
          <span v-for="item in benefitSkeletons" :key="item" class="skeleton-line skeleton-line-lg"></span>
        </div>
      </div>
    </div>

    <template v-else-if="catalog.currentProduct">
      <div class="container product-detail-layout">
        <div class="product-gallery-column">
          <div class="product-main-image">
            <LazyImage :src="activeImage" :alt="catalog.currentProduct.name" eager fit="contain" natural-height />
          </div>

          <div class="product-thumb-row">
            <button
              v-for="image in productGallery"
              :key="image"
              :class="['product-thumb', { active: image === activeImage }]"
              type="button"
              @click="activeImage = image"
            >
              <LazyImage :src="image" :alt="catalog.currentProduct.name" aspect-ratio="1 / 1.18" />
            </button>
          </div>
        </div>

        <div class="product-buy-column">
          <p class="detail-category">{{ categoryLabel }}</p>
          <h1>{{ catalog.currentProduct.name }}</h1>

          <div class="detail-price-stack">
            <p class="detail-price">{{ formatCurrency(selectedSizePrice) }}</p>
            <p class="detail-code-line">
              <span>{{ detailCopy.codeLabel }}</span>
              <strong>{{ catalog.currentProduct.productCode || catalog.currentProduct.sku }}</strong>
            </p>
            <p class="detail-subprice">{{ selectedSizeLabel }} · {{ detailCopy.basePriceLabel }} {{ formatCurrency(selectedSizePrice) }}</p>
          </div>

          <div v-if="colorOptions.length" class="detail-option-group detail-color-section">
            <p class="detail-color-title">
              {{ detailCopy.colorLabel }}: <strong>{{ selectedColorLabel }}</strong>
            </p>
            <div class="detail-color-grid">
              <button
                v-for="(option, index) in colorOptions"
                :key="option.slug"
                :class="['detail-color-tile', { active: option.slug === catalog.currentProduct.slug }]"
                type="button"
                @click="handleColorChange(option)"
              >
                <span v-if="index === 0" class="detail-color-badge">Hot</span>
                <span class="detail-color-tile-image">
                  <LazyImage :src="option.image" :alt="option.colorName || option.productCode" aspect-ratio="3 / 4" />
                </span>
              </button>
            </div>
          </div>

          <div class="detail-option-group">
            <div class="detail-size-head">
              <strong>{{ locale.t('detail.size') }}: {{ selectedSizeLabel }}</strong>
              <span>{{ locale.t('detail.sizeFinder') }}</span>
            </div>

            <div class="detail-size-grid">
              <button
                v-for="size in catalog.currentProduct.sizes"
                :key="size"
                :class="['detail-size-button', { active: size === selectedSize }]"
                type="button"
                @click="selectedSize = size"
              >
                {{ size }}
              </button>
            </div>

            <div class="detail-stock-banner">
              <span class="detail-stock-inline">{{ detailCopy.stockLabel }}: {{ selectedSizeStock }}</span>
            </div>
          </div>

          <div class="detail-option-group detail-quantity-section">
            <div class="detail-size-head">
              <strong>{{ detailCopy.quantityLabel }}</strong>
              <span>{{ detailCopy.quantityHint }}</span>
            </div>

            <div class="detail-quantity-card">
              <div class="detail-quantity-stepper">
                <button type="button" class="detail-qty-button" :disabled="!canPurchase" @click="decreaseQuantity">-</button>
                <input
                  v-model.number="selectedQuantity"
                  class="detail-qty-input"
                  type="number"
                  min="1"
                  :max="maxSelectableQuantity"
                  :disabled="!canPurchase"
                  @change="normalizeQuantity"
                />
                <button type="button" class="detail-qty-button" :disabled="!canPurchase" @click="increaseQuantity">+</button>
              </div>
              <div class="detail-quantity-meta">
                <strong>{{ formatCurrency(activeUnitPrice) }}</strong>
                <span>{{ detailCopy.selectedSizeLabel }} {{ selectedSizeLabel }}</span>
              </div>
            </div>
          </div>

          <div class="detail-action-row detail-action-row-elevated">
            <button class="detail-action-button secondary" type="button" :disabled="!canPurchase" @click="addToCart">
              {{ locale.t('common.addToCart') }}
            </button>
            <button class="detail-action-button primary" type="button" :disabled="!canPurchase" @click="buyNow">
              {{ locale.t('common.buyNow') }}
            </button>
          </div>
          <p v-if="addToCartSuccess" class="detail-cart-feedback">{{ addToCartSuccess }}</p>

          <div class="detail-media-stack">
            <section v-if="catalog.currentProduct.sizeChartImage" class="detail-media-card">
              <button
                class="detail-media-head detail-media-toggle"
                type="button"
                :aria-expanded="sizeChartExpanded"
                @click="sizeChartExpanded = !sizeChartExpanded"
              >
                <strong>{{ detailCopy.sizeChartTitle }}</strong>
                <span :class="['detail-media-chevron', { expanded: sizeChartExpanded }]">⌄</span>
              </button>
              <div v-show="sizeChartExpanded" class="detail-media-body">
                <LazyImage
                  :src="catalog.currentProduct.sizeChartImage"
                  :alt="detailCopy.sizeChartTitle"
                  fit="contain"
                  natural-height
                />
              </div>
            </section>

            <section v-if="catalog.currentProduct.descriptionImage" class="detail-media-card">
              <button
                class="detail-media-head detail-media-toggle"
                type="button"
                :aria-expanded="descriptionExpanded"
                @click="descriptionExpanded = !descriptionExpanded"
              >
                <strong>{{ detailCopy.descriptionImageTitle }}</strong>
                <span :class="['detail-media-chevron', { expanded: descriptionExpanded }]">⌄</span>
              </button>
              <div v-show="descriptionExpanded" class="detail-media-body">
                <LazyImage
                  :src="catalog.currentProduct.descriptionImage"
                  :alt="detailCopy.descriptionImageTitle"
                  fit="contain"
                  natural-height
                />
              </div>
            </section>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import LazyImage from '../components/LazyImage.vue'
import { useCartStore } from '../stores/cart'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const CATEGORY_LABELS = {
  womenswear: 'Womenswear',
  menswear: 'Menswear',
  pants: 'Pants',
  denim: 'Denim',
  outerwear: 'Outerwear',
  shirts: 'Shirts',
  tops: 'Tops',
  accessories: 'Accessories',
}

function titleCaseFromKey(value) {
  return String(value || '')
    .replace(/[-_]+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const catalog = useCatalogStore()
const locale = useLocaleStore()
const activeImage = ref('')
const selectedSize = ref('')
const selectedQuantity = ref(1)
const addToCartSuccess = ref('')
let addToCartSuccessTimer = null
const sizeChartExpanded = ref(false)
const descriptionExpanded = ref(false)
const thumbSkeletons = [1, 2, 3, 4]
const sizeSkeletons = [1, 2, 3, 4, 5]
const benefitSkeletons = [1, 2, 3, 4]

const detailCopy = {
  colorLabel: 'Color',
  codeLabel: 'Code',
  basePriceLabel: 'Base price',
  stockLabel: 'Available Stock',
  selectedSizeLabel: 'Selected size:',
  quantityLabel: 'Quantity',
  quantityHint: 'Adjust quantity before adding to cart',
  sizeChartTitle: 'Size Chart',
  descriptionImageTitle: 'Description Image',
}

const productGallery = computed(() => {
  if (!catalog.currentProduct) return []
  return catalog.currentProduct.gallery?.length ? catalog.currentProduct.gallery : [catalog.currentProduct.image]
})

const colorOptions = computed(() => catalog.currentProduct?.colorOptions || [])
const selectedColorLabel = computed(() => catalog.currentProduct?.colorName || '--')
const categoryLabel = computed(() => {
  const key = String(catalog.currentProduct?.categoryKey || '').trim().toLowerCase()
  if (key && CATEGORY_LABELS[key]) return CATEGORY_LABELS[key]

  const raw = String(catalog.currentProduct?.categoryLabel || '').trim()
  if (raw && /^[\x00-\x7F]+$/.test(raw)) return raw
  if (key) return titleCaseFromKey(key)
  return 'Category'
})

const selectedSizeRecord = computed(() => {
  const sizePrices = catalog.currentProduct?.sizePrices || []
  if (!sizePrices.length) return null
  return sizePrices.find((item) => item.sizeCode === selectedSize.value) || null
})

const selectedSizePrice = computed(() => Number(selectedSizeRecord.value?.price ?? catalog.currentProduct?.price ?? 0))
const selectedSizeStock = computed(() => {
  if (!catalog.currentProduct) return 0
  const sizePrices = catalog.currentProduct.sizePrices || []
  if (!sizePrices.length) return Number(catalog.currentProduct.stock ?? 0)
  return Number(selectedSizeRecord.value?.stock ?? 0)
})
const selectedSizeLabel = computed(() => selectedSize.value || '--')
const canPurchase = computed(() => selectedSizeStock.value > 0)
const maxSelectableQuantity = computed(() => Math.max(1, selectedSizeStock.value || 1))

const activeUnitPrice = computed(() => selectedSizePrice.value)


function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function normalizeQuantity() {
  if (!canPurchase.value) {
    selectedQuantity.value = 1
    return
  }
  const max = Number(selectedSizeStock.value || 1)
  const value = Number(selectedQuantity.value || 1)
  selectedQuantity.value = Math.max(1, Math.min(value, max))
}

function decreaseQuantity() {
  if (!canPurchase.value) return
  selectedQuantity.value = Math.max(1, Number(selectedQuantity.value || 1) - 1)
}

function increaseQuantity() {
  if (!canPurchase.value) return
  const max = Number(selectedSizeStock.value || 1)
  selectedQuantity.value = Math.min(max, Number(selectedQuantity.value || 1) + 1)
}

function loadDetail() {
  catalog.loadProduct(route.params.slug, locale.current)
}

function handleColorChange(option) {
  if (!option?.slug) return
  if (option.slug === route.params.slug) {
    activeImage.value = option.image || catalog.currentProduct?.image || ''
    return
  }
  router.push(`/product/${option.slug}`)
}

function showAddToCartSuccess() {
  addToCartSuccess.value = 'Added to cart successfully'
  if (addToCartSuccessTimer) {
    window.clearTimeout(addToCartSuccessTimer)
  }
  addToCartSuccessTimer = window.setTimeout(() => {
    addToCartSuccess.value = ''
    addToCartSuccessTimer = null
  }, 1000)
}

function addToCart() {
  if (!catalog.currentProduct || !canPurchase.value) return
  normalizeQuantity()
  cart.addItem(
    {
      ...catalog.currentProduct,
      basePrice: selectedSizePrice.value,
      stock: selectedSizeStock.value,
    },
    selectedQuantity.value,
    selectedSize.value
  )
  showAddToCartSuccess()
}

function buyNow() {
  if (!catalog.currentProduct || !canPurchase.value) return
  normalizeQuantity()
  cart.setSingleItem(
    {
      ...catalog.currentProduct,
      basePrice: selectedSizePrice.value,
      stock: selectedSizeStock.value,
    },
    selectedQuantity.value,
    selectedSize.value
  )
  router.push('/checkout')
}

watch(
  () => catalog.currentProduct,
  (product) => {
    if (!product) return
    activeImage.value = product.gallery?.[0] || product.image
    selectedSize.value = product.sizes?.[0] || ''
    selectedQuantity.value = 1
    sizeChartExpanded.value = false
    descriptionExpanded.value = false
  },
  { immediate: true }
)

watch(selectedSizeStock, () => {
  normalizeQuantity()
})

watch(() => route.params.slug, loadDetail)
watch(() => locale.current, loadDetail)

onMounted(() => {
  loadDetail()
})
</script>
