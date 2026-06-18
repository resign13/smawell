<template>
  <section class="account-page">
    <div class="container account-layout">
      <article class="panel-card">
        <div class="account-orders-head">
          <div>
            <p class="eyebrow">{{ copy.overline }}</p>
            <h1>{{ copy.title }}</h1>
            <p class="helper">{{ copy.subtitle }}</p>
          </div>
        </div>

        <div class="account-toolbar">
          <select v-model="selectedTimeRange" class="field checkout-select account-filter-select">
            <option value="all">{{ copy.filters.time.all }}</option>
            <option value="7d">{{ copy.filters.time.days7 }}</option>
            <option value="30d">{{ copy.filters.time.days30 }}</option>
            <option value="90d">{{ copy.filters.time.days90 }}</option>
            <option value="year">{{ copy.filters.time.thisYear }}</option>
          </select>

          <select v-model="selectedStatus" class="field checkout-select account-filter-select">
            <option value="all">{{ copy.filters.status.all }}</option>
            <option v-for="item in statusOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </div>

        <p v-if="catalog.error" class="error-text">{{ catalog.error }}</p>

        <div v-if="filteredOrders.length" class="account-order-list">
          <article v-for="order in filteredOrders" :key="order.id" class="account-order-item">
            <div class="account-order-main">
              <div>
                <strong>{{ order.orderNo }}</strong>
                <p>{{ summarizeItems(order.items) }}</p>
                <p class="account-order-email">{{ order.contactValue || '--' }}</p>
              </div>
              <span class="account-order-status" :class="`status-${order.status}`">
                {{ formatStatus(order.status) }}
              </span>
            </div>

            <div class="account-order-meta">
              <span>{{ formatDate(order.createdAt) }}</span>
              <span>{{ copy.itemCountLabel }} {{ order.itemCount }}</span>
              <span>{{ copy.shippingFeeLabel }} {{ formatCurrency(order.shippingFee || 0) }}</span>
              <span>{{ formatCurrency(order.totalAmount) }}</span>
            </div>

            <p class="helper">{{ order.shippingAddress }}</p>

            <div class="account-order-actions">
              <button class="secondary-button inline-button" type="button" @click="toggleExpanded(order.id)">
                {{ expandedOrderIds.has(order.id) ? copy.hideDetails : copy.viewDetails }}
              </button>
              <a
                v-if="order.paymentLink && order.status === 'pending_payment'"
                class="primary-button inline-button"
                :href="order.paymentLink"
                target="_blank"
                rel="noreferrer"
              >
                {{ copy.payNow }}
              </a>
              <button
                v-if="order.canCancel"
                class="text-button account-cancel-button"
                type="button"
                :disabled="cancellingOrderId === order.id"
                @click="handleCancel(order.id)"
              >
                {{ cancellingOrderId === order.id ? copy.loading : copy.cancelOrder }}
              </button>
            </div>

            <div v-if="expandedOrderIds.has(order.id)" class="account-order-detail">
              <div class="account-detail-grid">
                <div>
                  <span>{{ copy.contactLabel }}</span>
                  <strong>{{ order.contactValue || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.phoneLabel }}</span>
                  <strong>{{ order.phone || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.countryLabel }}</span>
                  <strong>{{ order.country || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.trackingLabel }}</span>
                  <strong>{{ order.trackingNo || copy.trackingEmpty }}</strong>
                </div>
                <div>
                  <span>{{ copy.paymentLabel }}</span>
                  <strong>{{ order.paymentLink ? copy.paymentReady : copy.paymentWaiting }}</strong>
                </div>
                <div>
                  <span>{{ copy.noteLabel }}</span>
                  <strong>{{ order.note || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.labelImagesLabel }}</span>
                  <strong v-if="orderLabelImages(order).length" class="order-label-images">
                    <a
                      v-for="(imageUrl, imageIndex) in orderLabelImages(order)"
                      :key="imageUrl"
                      :href="imageUrl"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {{ copy.viewImage }} {{ imageIndex + 1 }}
                    </a>
                  </strong>
                  <strong v-else>--</strong>
                </div>
                <div>
                  <span>{{ copy.itemsSubtotalLabel }}</span>
                  <strong>{{ formatCurrency(itemsSubtotal(order)) }}</strong>
                </div>
                <div>
                  <span>{{ copy.shippingFeeLabel }}</span>
                  <strong>{{ formatCurrency(order.shippingFee || 0) }}</strong>
                </div>
                <div>
                  <span>{{ copy.orderTotalLabel }}</span>
                  <strong>{{ formatCurrency(order.totalAmount) }}</strong>
                </div>
                <div>
                  <span>{{ copy.shippedAtLabel }}</span>
                  <strong>{{ formatDateTime(order.shippedAt) }}</strong>
                </div>
                <div>
                  <span>{{ copy.completedAtLabel }}</span>
                  <strong>{{ formatDateTime(order.completedAt) }}</strong>
                </div>
                <div>
                  <span>{{ copy.addressLabel }}</span>
                  <strong>{{ order.address || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.apartmentLabel }}</span>
                  <strong>{{ order.apartment || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.cityLabel }}</span>
                  <strong>{{ order.city || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.stateLabel }}</span>
                  <strong>{{ order.state || '--' }}</strong>
                </div>
                <div>
                  <span>{{ copy.zipLabel }}</span>
                  <strong>{{ order.zip || '--' }}</strong>
                </div>
              </div>

              <div class="account-order-items">
                <div class="account-order-items-head">
                  <strong>{{ copy.itemsTitle }}</strong>
                </div>

                <article
                  v-for="item in order.items"
                  :key="`${order.id}-${item.productId}-${item.sku}-${item.sizeCode}`"
                  class="account-order-line"
                >
                  <img v-if="item.image" :src="item.image" :alt="item.productName" class="account-order-line-image" />
                  <div class="account-order-line-copy">
                    <strong>{{ item.productName }}</strong>
                    <span>SKU {{ item.sku }}</span>
                    <span v-if="item.sizeCode">{{ copy.sizeLabel }} {{ item.sizeCode }}</span>
                  </div>
                  <div class="account-order-line-meta">
                    <span>{{ copy.quantityLabel }} {{ item.quantity }}</span>
                    <strong>{{ formatCurrency(item.totalPrice) }}</strong>
                  </div>
                </article>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="panel-card empty-state-card">
          <h3>{{ isFiltering ? copy.filterEmptyTitle : copy.emptyTitle }}</h3>
          <p class="helper">{{ isFiltering ? copy.filterEmptyText : copy.ordersEmptyText }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { useCatalogStore } from '../stores/catalog'

const catalog = useCatalogStore()

const expandedOrderIds = ref(new Set())
const cancellingOrderId = ref(0)
const selectedTimeRange = ref('all')
const selectedStatus = ref('all')

const copy = {
  overline: 'ORDER CENTER',
  title: 'Orders',
  subtitle: 'Review payment progress, shipping status and order details.',
  emptyTitle: 'No orders yet',
  ordersEmptyText: 'No orders yet. Start by browsing products.',
  filterEmptyTitle: 'No orders match the selected filters',
  filterEmptyText: 'Try another time range or status.',
  itemCountLabel: 'Items',
  viewDetails: 'View Details',
  hideDetails: 'Hide Details',
  cancelOrder: 'Cancel Order',
  payNow: 'Pay Now',
  loading: 'Loading...',
  contactLabel: 'Email',
  phoneLabel: 'Phone',
  countryLabel: 'Country / Region',
  trackingLabel: 'Tracking No.',
  trackingEmpty: 'Pending shipment',
  paymentLabel: 'Payment',
  paymentReady: 'Payment link available',
  paymentWaiting: 'Awaiting payment link',
  noteLabel: 'Order Note',
  labelImagesLabel: 'Attachments',
  viewImage: 'Open Attachment',
  itemsSubtotalLabel: 'Items Subtotal',
  shippingFeeLabel: 'Shipping Fee',
  orderTotalLabel: 'Order Total',
  shippedAtLabel: 'Shipped At',
  completedAtLabel: 'Completed At',
  addressLabel: 'Address',
  apartmentLabel: 'Apartment / Suite',
  cityLabel: 'City',
  stateLabel: 'State',
  zipLabel: 'ZIP code',
  itemsTitle: 'Order Items',
  sizeLabel: 'Size',
  quantityLabel: 'Qty',
  statusMap: {
    pending_payment: 'Pending Payment',
    paid: 'Paid',
    shipped: 'Shipped',
    completed: 'Completed',
    cancelled: 'Cancelled',
  },
  filters: {
    time: {
      all: 'All Time',
      days7: 'Last 7 Days',
      days30: 'Last 30 Days',
      days90: 'Last 90 Days',
      thisYear: 'This Year',
    },
    status: {
      all: 'All Status',
    },
  },
}

const statusOptions = computed(() =>
  ['pending_payment', 'paid', 'shipped', 'completed', 'cancelled'].map((value) => ({
    value,
    label: copy.statusMap[value] || value,
  }))
)
const isFiltering = computed(() => selectedTimeRange.value !== 'all' || selectedStatus.value !== 'all')

const filteredOrders = computed(() =>
  catalog.orders.filter((order) => {
    const statusMatch = selectedStatus.value === 'all' || order.status === selectedStatus.value
    const timeMatch = matchesTimeRange(order.createdAt, selectedTimeRange.value)
    return statusMatch && timeMatch
  })
)

function matchesTimeRange(value, range) {
  if (range === 'all') return true
  const target = new Date(value)
  if (Number.isNaN(target.getTime())) return false
  const now = new Date()
  const msPerDay = 24 * 60 * 60 * 1000
  const diffDays = (now.getTime() - target.getTime()) / msPerDay
  if (range === '7d') return diffDays <= 7
  if (range === '30d') return diffDays <= 30
  if (range === '90d') return diffDays <= 90
  if (range === 'year') return target.getFullYear() === now.getFullYear()
  return true
}

function formatCurrency(value) {
  const amount = Number(value || 0)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(amount)
}

function formatDate(value) {
  const date = value ? new Date(value) : null
  if (!date || Number.isNaN(date.getTime())) return '--'
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function formatDateTime(value) {
  const date = value ? new Date(value) : null
  if (!date || Number.isNaN(date.getTime())) return '--'
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function formatStatus(status) {
  return copy.statusMap[status] || status
}

function itemsSubtotal(order) {
  return (order.items || []).reduce((sum, item) => sum + Number(item.totalPrice || 0), 0)
}

function orderLabelImages(order) {
  if (Array.isArray(order.labelImageUrls)) return order.labelImageUrls.filter(Boolean).slice(0, 5)
  return order.labelPdfUrl ? [order.labelPdfUrl] : []
}

function summarizeItems(items) {
  return items.map((item) => item.productName).filter(Boolean).join(' / ')
}

function toggleExpanded(orderId) {
  const next = new Set(expandedOrderIds.value)
  if (next.has(orderId)) next.delete(orderId)
  else next.add(orderId)
  expandedOrderIds.value = next
}

async function handleCancel(orderId) {
  cancellingOrderId.value = orderId
  const updated = await catalog.cancelOrder(orderId)
  if (updated) {
    const next = new Set(expandedOrderIds.value)
    next.add(orderId)
    expandedOrderIds.value = next
  }
  cancellingOrderId.value = 0
}

onMounted(() => {
  catalog.loadMyOrders()
})
</script>
