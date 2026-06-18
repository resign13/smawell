<template>
  <section class="shop-page">
    <div class="container">
      <section v-if="isSectionPage" class="shop-section-head">
        <p class="eyebrow">{{ sectionPageEyebrow }}</p>
        <h1>{{ sectionPageTitle }}</h1>
      </section>

      <section class="shop-filter-row shop-filter-row-search">
        <form class="shop-search-bar" @submit.prevent="submitSearch">
          <input
            v-model="searchDraft"
            class="field shop-search-input"
            type="search"
            :placeholder="locale.t('common.search')"
          />
          <button class="primary-button shop-search-button" type="submit">
            {{ locale.t('nav.search') }}
          </button>
          <button
            v-if="searchDraft || keyword"
            class="secondary-button shop-clear-button"
            type="button"
            @click="clearSearch"
          >
            {{ locale.t('common.back') }}
          </button>
        </form>
      </section>

      <section class="shop-filter-row">
        <label class="shop-stock-toggle">
          <input v-model="stockOnly" type="checkbox" />
          <span>{{ locale.t('common.stockOnly') }}</span>
        </label>

        <label class="shop-sort-box">
          <span>Sort By</span>
          <select v-model="sortOrder">
            <option value="newest">Newest</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="price-asc">Price: Low to High</option>
          </select>
        </label>
      </section>

      <div v-if="catalog.loading" class="shop-product-grid skeleton-grid">
        <article
          v-for="item in productSkeletons"
          :key="item"
          class="product-card skeleton-product-card"
        >
          <div class="product-card-media skeleton-media"></div>
          <div class="product-card-copy skeleton-product-copy">
            <span class="skeleton-line skeleton-line-lg"></span>
            <span class="skeleton-line skeleton-line-sm"></span>
            <span class="skeleton-line skeleton-line-xs"></span>
          </div>
        </article>
      </div>

      <template v-else>
        <div v-if="sortedProducts.length" class="shop-results-head">
          <p>{{ paginationLabels.itemLabelDisplay }} {{ sortedProducts.length }}</p>
        </div>

        <div v-if="paginatedProducts.length" class="shop-product-grid">
          <ProductCard
            v-for="product in paginatedProducts"
            :key="product.id"
            :product="product"
          />
        </div>

        <StorefrontPagination
          v-if="sortedProducts.length"
          :page="currentPage"
          :page-size="pageSize"
          :size-options="[20, 40, 60]"
          :total-items="sortedProducts.length"
          :labels="paginationLabels"
          @update:page="currentPage = $event"
          @update:page-size="pageSize = $event"
        />

        <div v-else class="panel-card shop-empty-state">
          <h3>{{ locale.t('nav.search') }}</h3>
          <p>{{ locale.t('common.search') }}</p>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductCard from '../components/ProductCard.vue'
import StorefrontPagination from '../components/StorefrontPagination.vue'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const route = useRoute()
const router = useRouter()
const catalog = useCatalogStore()
const locale = useLocaleStore()

const sectionKeyBySlug = {
  'best-seller': 'bestSeller',
  'new-arrival': 'newArrival',
  'special-price': 'specialPrice',
}

const sectionTitleByKey = {
  bestSeller: 'BEST SELLER',
  newArrival: 'NEW ARRIVAL',
  specialPrice: 'PRE-ORDER',
}

const category = ref(route.query.category?.toString() || '')
const keyword = ref(route.query.keyword?.toString() || '')
const searchDraft = ref(route.query.keyword?.toString() || '')
const stockOnly = ref(false)
const sortOrder = ref('newest')
const currentPage = ref(1)
const pageSize = ref(20)
const productSkeletons = [1, 2, 3, 4, 5, 6, 7, 8]

const paginationLabels = computed(() => ({
  prev: 'Prev',
  next: 'Next',
  of: 'of',
  perPage: 'Per page',
  itemLabel: 'products',
  itemLabelDisplay: 'Products',
}))

const sectionSlug = computed(() => route.params.sectionSlug?.toString() || '')
const sectionKey = computed(() => sectionKeyBySlug[sectionSlug.value] || '')
const isSectionPage = computed(() => Boolean(sectionKey.value))
const sectionPageEyebrow = computed(() => 'CURATED COLLECTION')
const sectionPageTitle = computed(() => sectionTitleByKey[sectionKey.value] || 'SHOP')

const baseProducts = computed(() => {
  if (isSectionPage.value) {
    return catalog.collectionSections?.[sectionKey.value] || []
  }
  return catalog.products || []
})

const sortedProducts = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()
  const items = baseProducts.value.filter((item) => {
    if (stockOnly.value && Number(item.stock || 0) < 1) return false
    if (!isSectionPage.value && category.value && item.categoryKey !== category.value) return false

    if (normalizedKeyword) {
      const haystack = [
        item.name,
        item.summary,
        item.productCode,
        item.sku,
        item.colorName,
        item.categoryLabel,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      if (!haystack.includes(normalizedKeyword)) return false
    }

    return true
  })

  if (sortOrder.value === 'newest') {
    return [...items].sort((a, b) => {
      const aTime = Date.parse(a.createdAt || a.updatedAt || '') || 0
      const bTime = Date.parse(b.createdAt || b.updatedAt || '') || 0
      if (bTime !== aTime) return bTime - aTime
      return Number(b.id || 0) - Number(a.id || 0)
    })
  }

  if (sortOrder.value === 'price-asc') {
    return [...items].sort((a, b) => Number(a.price || 0) - Number(b.price || 0))
  }

  if (sortOrder.value === 'price-desc') {
    return [...items].sort((a, b) => Number(b.price || 0) - Number(a.price || 0))
  }

  return items
})

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedProducts.value.slice(start, start + pageSize.value)
})

function buildQuery() {
  const query = {}
  if (!isSectionPage.value && category.value) query.category = category.value
  if (keyword.value) query.keyword = keyword.value
  return query
}

async function loadList() {
  if (isSectionPage.value) {
    await catalog.loadCollectionSection(sectionSlug.value, locale.current)
    return
  }

  await catalog.loadProducts(
    { category: category.value, keyword: keyword.value },
    locale.current
  )
}

function submitSearch() {
  keyword.value = searchDraft.value.trim()
  router.replace({ path: route.path, query: buildQuery() })
}

function clearSearch() {
  searchDraft.value = ''
  keyword.value = ''
  router.replace({ path: route.path, query: buildQuery() })
}

watch(() => locale.current, loadList)

watch([stockOnly, sortOrder, pageSize], () => {
  currentPage.value = 1
})

watch(
  () => [route.params.sectionSlug, route.query.category, route.query.keyword],
  ([nextSectionSlug, nextCategory, nextKeyword]) => {
    const hasSection = Boolean(sectionKeyBySlug[nextSectionSlug?.toString() || ''])
    category.value = hasSection ? '' : nextCategory?.toString() || ''
    keyword.value = nextKeyword?.toString() || ''
    searchDraft.value = keyword.value
    currentPage.value = 1
    loadList()
  }
)

watch(
  () => sortedProducts.value.length,
  (count) => {
    const totalPages = Math.max(1, Math.ceil(count / pageSize.value))
    if (currentPage.value > totalPages) {
      currentPage.value = totalPages
    }
  },
  { immediate: true }
)

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.shop-section-head {
  display: grid;
  gap: 8px;
  padding-bottom: 6px;
}

.shop-section-head h1 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3.6rem);
  line-height: 0.96;
  letter-spacing: -0.04em;
}

.shop-results-head {
  margin: 18px 0 0;
}

.shop-results-head p {
  margin: 0;
  color: var(--muted);
  font-size: 0.96rem;
}
</style>
