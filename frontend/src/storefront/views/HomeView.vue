<template>
  <section class="home-page">
    <div class="container home-body-stack">
      <section class="home-search-section">
        <form class="home-search-bar" @submit.prevent="submitHomeSearch">
          <input
            v-model.trim="homeSearchDraft"
            class="field home-search-input"
            type="search"
            :placeholder="locale.t('common.search')"
          />
          <button class="home-search-button" type="submit">
            {{ locale.t('nav.search') }}
          </button>
        </form>
      </section>
    </div>

    <section class="home-hero-section">
      <div v-if="showHomeSkeleton" class="container home-hero-tabs home-hero-tabs-skeleton">
        <span v-for="item in heroTabSkeletons" :key="item" class="skeleton-button home-hero-tab-skeleton"></span>
      </div>

      <div v-else class="container home-hero-tabs">
        <button
          v-for="(slide, index) in heroSlides"
          :key="slide.slotKey"
          :class="['home-hero-tab', { active: index === currentSlide }]"
          type="button"
          @click="setSlide(index)"
        >
          {{ slide.tabLabel }}
        </button>
      </div>

      <section class="container home-hero-shell home-hero-shell-full">
        <div v-if="showHomeSkeleton" class="home-hero-skeleton">
          <div class="skeleton-media home-hero-skeleton-media"></div>
        </div>

        <template v-else>
          <article
          v-for="(slide, index) in heroSlides"
          :key="slide.slotKey"
          :class="['home-hero-slide', { active: index === currentSlide }]"
          role="link"
          tabindex="0"
          @click="handleHeroClick(slide.slotKey)"
          @keydown.enter.prevent="handleHeroClick(slide.slotKey)"
          @keydown.space.prevent="handleHeroClick(slide.slotKey)"
        >
          <LazyImage
            :src="slide.image"
            :alt="slide.title"
            wrapper-class="home-hero-media"
            img-class="home-hero-image"
            :eager="index === 0"
          />
          </article>

          <button
            v-if="heroSlides.length > 1"
            class="home-hero-nav home-hero-nav-prev"
            type="button"
            aria-label="Previous slide"
            @click.stop="goPrev"
          >
            <span aria-hidden="true">&#8249;</span>
          </button>

          <button
            v-if="heroSlides.length > 1"
            class="home-hero-nav home-hero-nav-next"
            type="button"
            aria-label="Next slide"
            @click.stop="goNext"
          >
            <span aria-hidden="true">&#8250;</span>
          </button>

          <div v-if="heroSlides.length > 1" class="home-hero-progress">
            <button
              v-for="(slide, index) in heroSlides"
              :key="`${slide.slotKey}-progress`"
              :class="['home-hero-progress-item', { active: index === currentSlide }]"
              type="button"
              @click="setSlide(index)"
            >
              <span></span>
            </button>
          </div>
        </template>
      </section>
    </section>

    <div class="container home-body-stack">
      <section v-if="showHomeSkeleton" class="home-category-strip home-category-strip-top">
        <article
          v-for="item in categorySkeletons"
          :key="item"
          class="home-category-card home-category-card-top home-category-card-skeleton"
        >
          <div class="skeleton-media home-category-skeleton-media"></div>
        </article>
      </section>

      <section v-else class="home-category-strip home-category-strip-top">
        <RouterLink
          v-for="card in categoryCards"
          :key="card.key"
          class="home-category-card home-category-card-top"
          :to="card.to"
        >
          <LazyImage :src="card.image" :alt="card.label" aspect-ratio="1 / 0.72" />
          <div class="home-category-overlay">
            <strong>{{ card.label }}</strong>
            <span>{{ card.caption }}</span>
          </div>
        </RouterLink>
      </section>

      <section
        v-for="section in productSections"
        :id="section.id"
        :key="section.key"
        class="home-best-seller"
      >
        <div class="section-title-row">
          <h2>{{ section.title }}</h2>
          <RouterLink class="text-link" :to="section.viewAllPath">{{ homeCopy.viewAll }}</RouterLink>
        </div>

        <div v-if="showHomeSkeleton" class="home-product-grid skeleton-grid">
          <article v-for="item in productSkeletons" :key="`${section.key}-${item}`" class="product-card skeleton-product-card">
            <div class="product-card-media skeleton-media"></div>
            <div class="product-card-copy skeleton-product-copy">
              <span class="skeleton-line skeleton-line-lg"></span>
              <span class="skeleton-line skeleton-line-sm"></span>
              <span class="skeleton-line skeleton-line-xs"></span>
            </div>
          </article>
        </div>
        <div v-else class="home-product-grid">
          <ProductCard
            v-for="product in section.products"
            :key="`${section.key}-${product.id}`"
            :product="product"
            :show-badge="false"
          />
        </div>
      </section>

      <section v-if="showHomeSkeleton" id="about" class="home-brand-section home-brand-skeleton">
        <article class="home-brand-copy">
          <span class="skeleton-line skeleton-line-xs"></span>
          <span class="skeleton-line skeleton-line-title"></span>
          <span class="skeleton-line skeleton-line-lg"></span>
          <span class="skeleton-line skeleton-line-md"></span>
          <span class="skeleton-line skeleton-line-lg"></span>
          <span class="skeleton-line skeleton-line-md"></span>
        </article>

        <article class="home-brand-stats">
          <div class="home-stat-list">
            <div v-for="item in statSkeletons" :key="item" class="home-stat-item skeleton-stat-item">
              <span class="skeleton-line skeleton-line-number"></span>
              <span class="skeleton-line skeleton-line-sm"></span>
            </div>
          </div>
        </article>
      </section>

      <section v-else id="about" class="home-brand-section">
        <article class="home-brand-copy">
          <p class="eyebrow">{{ homeCopy.storyTitle }}</p>
          <span class="home-brand-rule"></span>
          <div class="home-brand-body">
            <p class="home-brand-lead">{{ conciseBrandStoryParagraphs[0] }}</p>
            <p v-for="paragraph in conciseBrandStoryParagraphs.slice(1)" :key="paragraph">{{ paragraph }}</p>
          </div>
        </article>

        <article class="home-brand-stats">
          <div class="home-stat-list">
            <div v-for="stat in visibleStats" :key="stat.label" class="home-stat-item">
              <strong>{{ stat.value }}</strong>
              <span>{{ stat.label }}</span>
            </div>
          </div>
        </article>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import LazyImage from '../components/LazyImage.vue'
import ProductCard from '../components/ProductCard.vue'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const catalog = useCatalogStore()
const locale = useLocaleStore()
const router = useRouter()
const currentSlide = ref(0)
const homeSearchDraft = ref('')
const homeResolved = ref(false)
const heroTabSkeletons = [1, 2, 3]
const categorySkeletons = [1, 2, 3, 4, 5]
const productSkeletons = [1, 2, 3, 4, 5]
const statSkeletons = [1, 2]
const sectionSlugByKey = {
  bestSeller: 'best-seller',
  newArrival: 'new-arrival',
  specialPrice: 'special-price',
}

const brandStoryCopy = computed(() => ({
  paragraphs: [
    'SMAWELL was built from a long-term view of modern apparel. We believe strong products should do more than follow short-lived trends. They should balance silhouette, fabric, color, comfort and supply stability in a way that makes them commercially meaningful over time. That is why the brand was never limited to a single narrow category, and why the storefront now brings together both menswear and womenswear in one more complete merchandise structure.',
    'From a product perspective, SMAWELL focuses on building a repeatable core assortment. Whether it is pants for everyday business-casual use, tops with cleaner silhouettes, denim with dependable turnover, or outerwear suited to seasonal transitions, the goal is not only to create pieces that look good, but pieces that can support real sell-through and ongoing replenishment. For buyers, this means a clearer category system, a steadier launch rhythm, and a more usable product matrix for assortment planning.',
    'At the same time, SMAWELL treats presentation as part of the product itself. We want buyers to understand the brand quickly the moment they enter the site, not just scroll through disconnected item cards. That is why the homepage is organized around hero imagery, category navigation, best-seller and new-arrival modules, visible inventory and a smoother order flow. The storefront is meant to function not only as a sales page, but as the first layer of trust between the brand and its customers.',
  ],
  quote: 'Designed for modern wardrobes, built for lasting business.',
}))

const conciseBrandStoryCopy = computed(() => ({
  paragraphs: [
    'SMAWELL focuses on modern apparel with cleaner silhouettes, steadier supply and a more unified presentation across menswear and womenswear.',
    'The storefront is designed to help buyers understand the brand quickly, browse key categories with clarity, and move through inventory and ordering with less friction.',
  ],
  quote: 'Modern apparel, steady supply.',
}))

const homeCopy = computed(() => ({
  title: 'A modern apparel storefront for womenswear and menswear',
  storyTitle: 'Brand Story',
  storyText: 'SMAWELL uses a more premium homepage structure to present banners, category navigation, best sellers and special-price products in one clean storefront flow.',
  storyQuote: 'Modern apparel, stable supply, stronger presentation.',
  strengthCards: [
    { title: 'Admin-Controlled Homepage', text: 'Hero banners, category strip and all 3 product modules can be managed from the admin system.' },
    { title: 'Women + Men Categories', text: 'The homepage now covers womenswear, menswear, pants, denim and outerwear together.' },
    { title: 'Direct Order Sync', text: 'Cart checkout still pushes orders straight into the backend workflow.' },
  ],
  tabs: {
    bestSeller: 'BEST SELLER',
    newArrival: 'NEW ARRIVAL',
    specialPrice: 'PRE-ORDER',
  },
  sectionTitles: {
    bestSeller: 'BEST SELLER',
    newArrival: 'NEW ARRIVAL',
    specialPrice: 'PRE-ORDER',
  },
  fallbackOverlines: {
    bestSeller: 'BEST SELLER',
    newArrival: 'NEW ARRIVAL',
    specialPrice: 'PRE-ORDER',
  },
  fallbackTitles: {
    bestSeller: 'Lead with your strongest best-selling styles',
    newArrival: 'Spotlight the latest arrivals from the current season',
    specialPrice: 'Use special-price products to push faster conversion',
  },
  fallbackTexts: {
    bestSeller: 'Guide buyers from the hero directly into the best-selling product block.',
    newArrival: 'Keep the homepage fresh with a dedicated new-arrival section.',
    specialPrice: 'Use a focused sale block to support promotional conversion.',
  },
  shopNow: 'SHOP NOW',
  viewAll: 'View All',
  categoryCaptions: {
    womenswear: 'Blouses and elevated tops',
    menswear: 'Core tees and polos',
    pants: 'Tailored and relaxed silhouettes',
    denim: 'Washed fits and daily staples',
    outerwear: 'Sets, jackets and layers',
  },
}))

const categoryMedia = {
  womenswear: '/media/storefront/womenswear-blouse-1.jpg',
  menswear: '/media/storefront/menswear-white-tee.jpg',
  pants: '/media/storefront/womenswear-pants-1.jpg',
  denim: '/media/storefront/womenswear-denim-1.jpg',
  outerwear: '/media/storefront/outerwear-leather-2.jpg',
}

const brandStoryParagraphs = computed(() => brandStoryCopy.value.paragraphs)
const brandStoryQuote = computed(() => brandStoryCopy.value.quote)
const conciseBrandStoryParagraphs = computed(() => conciseBrandStoryCopy.value.paragraphs)
const conciseBrandStoryQuote = computed(() => conciseBrandStoryCopy.value.quote)
const visibleStats = computed(() => (catalog.stats || []).slice(0, 2))
const sectionOrder = ['bestSeller', 'newArrival', 'specialPrice']
const hasHomeContent = computed(
  () =>
    heroSlides.value.length > 0 ||
    categoryCards.value.length > 0 ||
    productSections.value.some((section) => section.products.length > 0) ||
    visibleStats.value.length > 0
)
const showHomeSkeleton = computed(() => !homeResolved.value && (!hasHomeContent.value || catalog.loading))

const heroSlides = computed(() =>
  sectionOrder.map((key) => {
    const banner = catalog.banners.find((item) => item.slotKey === key) || {}
    return {
      slotKey: key,
      image: banner.image || '',
      overline: homeCopy.value.fallbackOverlines[key],
      title: banner.title || homeCopy.value.fallbackTitles[key],
      text: banner.subtitle || homeCopy.value.fallbackTexts[key],
      ctaLabel: banner.ctaLabel || homeCopy.value.shopNow,
      tabLabel: homeCopy.value.tabs[key],
    }
  }).filter((item) => item.image)
)

const categoryCards = computed(() =>
  (catalog.homeCategories || []).map((card) => ({
    ...card,
    image: card.imageUrl || categoryMedia[card.key] || categoryMedia.womenswear,
    caption: homeCopy.value.categoryCaptions[card.key] || card.label,
    to: `/shop${card.key ? `?category=${card.key}` : ''}`,
  }))
)

const productSections = computed(() =>
  sectionOrder.map((key) => ({
    key,
    id: sectionId(key),
    title: homeCopy.value.sectionTitles[key],
    viewAllPath: `/collections/${sectionSlugByKey[key]}`,
    products: (catalog.homeSections?.[key] || []).slice(0, 5),
  }))
)

let timer = null

function sectionId(key) {
  return (
    {
      bestSeller: 'best-seller',
      newArrival: 'new-arrival',
      specialPrice: 'special-price',
    }[key] || key
  )
}

function handleHeroClick(key) {
  const slug = sectionSlugByKey[key]
  if (!slug) return
  router.push(`/collections/${slug}`)
}

function submitHomeSearch() {
  const keyword = homeSearchDraft.value.trim()
  router.push({
    path: '/shop',
    query: keyword ? { keyword } : {},
  })
}

function restartRotation() {
  stopRotation()
  startRotation()
}

function setSlide(index) {
  currentSlide.value = index
  restartRotation()
}

function goPrev() {
  if (!heroSlides.value.length) return
  currentSlide.value =
    (currentSlide.value - 1 + heroSlides.value.length) % heroSlides.value.length
  restartRotation()
}

function goNext() {
  if (!heroSlides.value.length) return
  currentSlide.value = (currentSlide.value + 1) % heroSlides.value.length
  restartRotation()
}

function startRotation() {
  stopRotation()
  if (heroSlides.value.length < 2) return
  timer = window.setInterval(() => {
    currentSlide.value = (currentSlide.value + 1) % heroSlides.value.length
  }, 5000)
}

function stopRotation() {
  if (timer) {
    window.clearInterval(timer)
    timer = null
  }
}

async function loadHome() {
  try {
    await catalog.loadHome(locale.current)
    currentSlide.value = 0
    startRotation()
  } finally {
    homeResolved.value = true
  }
}

watch(() => locale.current, loadHome)
watch(
  () => heroSlides.value.length,
  () => {
    if (currentSlide.value >= heroSlides.value.length) {
      currentSlide.value = 0
    }
  }
)

onMounted(() => {
  loadHome()
})

onBeforeUnmount(() => {
  stopRotation()
})
</script>

<style scoped>
#about {
  scroll-margin-top: 120px;
}
</style>
