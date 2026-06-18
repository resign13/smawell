import { defineStore } from 'pinia'

import { request } from '../api'
import {
  applyHomeImageOverrides,
  applyProductDetailImageOverrides,
  applyProductsImageOverrides,
} from '../imageOverrides'
import { useAuthStore } from './auth'


function normalizeCategoryLabel(item = {}) {
  const key = String(item?.key || item?.categoryKey || '').trim().toLowerCase()
  const labels = {
    womenswear: 'Womenswear',
    menswear: 'Menswear',
    pants: 'Pants',
    denim: 'Denim',
    outerwear: 'Outerwear',
    shirts: 'Shirts',
    tops: 'Tops',
    accessories: 'Accessories',
  }
  const fallback = key
    ? key.replace(/[-_]+/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
    : 'Category'
  return {
    ...item,
    label: labels[key] || item?.label || fallback,
    categoryLabel: labels[key] || item?.categoryLabel || item?.label || fallback,
  }
}

function normalizeProductCategory(item = {}) {
  const normalized = normalizeCategoryLabel({
    key: item.categoryKey,
    categoryKey: item.categoryKey,
    label: item.categoryLabel,
    categoryLabel: item.categoryLabel,
  })
  return {
    ...item,
    categoryLabel: normalized.categoryLabel,
  }
}


export const useCatalogStore = defineStore('catalog', {
  state: () => ({
    banners: [],
    featured: [],
    homeSections: {
      bestSeller: [],
      newArrival: [],
      specialPrice: [],
    },
    collectionSections: {
      bestSeller: [],
      newArrival: [],
      specialPrice: [],
    },
    categories: [],
    homeCategories: [],
    stats: [],
    products: [],
    currentProduct: null,
    related: [],
    orders: [],
    loading: false,
    detailLoading: false,
    orderSubmitting: false,
    orderSuccessMessage: '',
    error: '',
  }),
  actions: {
    primeHomeLoading() {
      this.loading = true
      this.error = ''
    },
    authHeaders() {
      const auth = useAuthStore()
      return auth.token
        ? {
            Authorization: `Bearer ${auth.token}`,
          }
        : {}
    },
    async loadHome(lang) {
      this.loading = true
      this.error = ''
      try {
        const raw = await request(`/api/home?lang=${encodeURIComponent(lang)}`)
        const data = applyHomeImageOverrides(raw)
        this.banners = data.banners
        this.featured = data.featured || data.sections?.bestSeller || []
        this.homeSections = {
          bestSeller: (data.sections?.bestSeller || []).map((item) => normalizeProductCategory(item)),
          newArrival: (data.sections?.newArrival || []).map((item) => normalizeProductCategory(item)),
          specialPrice: (data.sections?.specialPrice || []).map((item) => normalizeProductCategory(item)),
        }
        this.collectionSections = {
          bestSeller: (data.collectionSections?.bestSeller || []).map((item) => normalizeProductCategory(item)),
          newArrival: (data.collectionSections?.newArrival || []).map((item) => normalizeProductCategory(item)),
          specialPrice: (data.collectionSections?.specialPrice || []).map((item) => normalizeProductCategory(item)),
        }
        this.homeCategories = (data.categories || []).map((item) => normalizeCategoryLabel(item))
        this.categories = (data.allCategories || data.categories || []).map((item) => normalizeCategoryLabel(item))
        this.stats = data.stats
      } catch (error) {
        this.error = error.message || 'Home load failed'
      } finally {
        this.loading = false
      }
    },
    async loadCollectionSection(sectionSlug, lang = 'zh') {
      this.loading = true
      this.error = ''
      try {
        const data = await request(
          `/api/collections/${encodeURIComponent(sectionSlug)}?lang=${encodeURIComponent(lang)}`,
          {
            headers: this.authHeaders(),
          }
        )
        this.collectionSections[data.sectionKey] = (data.items || []).map((item) => normalizeProductCategory(item))
      } catch (error) {
        this.error = error.message || 'Collection load failed'
      } finally {
        this.loading = false
      }
    },
    async loadProducts(filters = {}, lang = 'zh') {
      const params = new URLSearchParams({ lang })
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.set(key, value)
      })
      this.loading = true
      this.error = ''
      try {
        const raw = await request(`/api/products?${params.toString()}`, {
          headers: this.authHeaders(),
        })
        const data = applyProductsImageOverrides(raw)
        this.products = (data.items || []).map((item) => normalizeProductCategory(item))
      } catch (error) {
        this.error = error.message || 'Product load failed'
      } finally {
        this.loading = false
      }
    },
    async loadProduct(slug, lang = 'zh') {
      this.detailLoading = true
      this.error = ''
      try {
        const raw = await request(`/api/products/${slug}?lang=${encodeURIComponent(lang)}`, {
          headers: this.authHeaders(),
        })
        const data = applyProductDetailImageOverrides(raw)
        this.currentProduct = normalizeProductCategory(data.product || {})
        this.related = (data.related || []).map((item) => normalizeProductCategory(item))
      } catch (error) {
        this.currentProduct = null
        this.related = []
        this.error = error.message || 'Detail load failed'
      } finally {
        this.detailLoading = false
      }
    },
    async createOrder(payload) {
      this.orderSubmitting = true
      this.error = ''
      this.orderSuccessMessage = ''
      try {
        const data = await request('/api/orders', {
          method: 'POST',
          headers: this.authHeaders(),
          body: JSON.stringify(payload),
        })
        this.orderSuccessMessage = data.message
        await this.loadMyOrders()
        return data.order
      } catch (error) {
        this.error = error.message || 'Order submit failed'
        return null
      } finally {
        this.orderSubmitting = false
      }
    },
    async uploadOrderAttachment(files) {
      this.error = ''
      const formData = new FormData()
      const list = Array.isArray(files) ? files : [files]
      list.forEach((file) => formData.append('files', file))
      try {
        return await request('/api/order-attachments', {
          method: 'POST',
          headers: this.authHeaders(),
          body: formData,
        })
      } catch (error) {
        this.error = error.message || 'Attachment upload failed'
        return null
      }
    },
    async loadMyOrders(query = '') {
      const auth = useAuthStore()
      if (!auth.token) {
        this.orders = []
        return
      }
      try {
        const suffix = query ? `?q=${encodeURIComponent(query)}` : ''
        const data = await request(`/api/store/orders${suffix}`, {
          headers: this.authHeaders(),
        })
        this.orders = data.items
      } catch (error) {
        this.orders = []
        this.error = error.message || 'Order load failed'
      }
    },
    async cancelOrder(orderId) {
      this.error = ''
      try {
        const data = await request(`/api/store/orders/${orderId}/cancel`, {
          method: 'POST',
          headers: this.authHeaders(),
        })
        this.orders = this.orders.map((item) => (item.id === data.order.id ? data.order : item))
        return data.order
      } catch (error) {
        this.error = error.message || 'Order cancel failed'
        return null
      }
    },
    resetOrderState() {
      this.orders = []
      this.orderSubmitting = false
      this.orderSuccessMessage = ''
      this.error = ''
    },
    clearMessages() {
      this.error = ''
      this.orderSuccessMessage = ''
    },
  },
})
