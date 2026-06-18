<template>
  <section class="inventory-page">
    <div class="container">
      <section class="inventory-toolbar">
        <label class="inventory-field">
          <span>Category</span>
          <select v-model="categoryFilter">
            <option value="">All Categories</option>
            <option v-for="category in categoryOptions" :key="category.key" :value="category.key">
              {{ category.label }}
            </option>
          </select>
        </label>

        <label class="inventory-field inventory-search">
          <span>Search</span>
          <input
            v-model="keyword"
            type="search"
            placeholder="Search product title, SKU, color or category"
          />
        </label>
      </section>

      <section class="inventory-stat-grid">
        <article>
          <span>Color SKUs</span>
          <strong>{{ filteredRows.length }}</strong>
        </article>
        <article>
          <span>Total Available Stock</span>
          <strong>{{ totalStock }}</strong>
        </article>
        <article>
          <span>Size Columns</span>
          <strong>{{ sizeColumns.length }}</strong>
        </article>
      </section>

      <div v-if="catalog.loading" class="inventory-state">
        Loading inventory...
      </div>

      <template v-else>
        <div class="inventory-table-card">
          <div class="inventory-table-scroll">
            <table class="inventory-table">
              <thead>
                <tr>
                  <th>Product Title</th>
                  <th>Color SKU</th>
                  <th>Image</th>
                  <th>Color</th>
                  <th>Category</th>
                  <th v-for="column in sizeColumns" :key="column.key">{{ column.label }}</th>
                  <th>Available Stock</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in paginatedRows" :key="row.id">
                  <td>
                    <RouterLink class="inventory-product-link" :to="`/product/${row.slug}`">
                      {{ row.name }}
                    </RouterLink>
                  </td>
                  <td class="inventory-sku">{{ row.colorSku }}</td>
                  <td>
                    <RouterLink class="inventory-image-link" :to="`/product/${row.slug}`">
                      <LazyImage
                        v-if="row.image"
                        :src="row.image"
                        :alt="row.name"
                        wrapper-class="inventory-product-image"
                        aspect-ratio="1 / 1"
                        fit="cover"
                      />
                      <span v-else class="inventory-image-empty">No Image</span>
                    </RouterLink>
                  </td>
                  <td>{{ row.colorName || '—' }}</td>
                  <td>{{ row.categoryLabel }}</td>
                  <td v-for="column in sizeColumns" :key="`${row.id}-${column.key}`">
                    <span v-if="row.sizeStocks[column.key]" class="inventory-stock-pill">
                      {{ row.sizeStocks[column.key] }}
                    </span>
                    <span v-else class="inventory-empty-size">—</span>
                  </td>
                  <td class="inventory-total">{{ row.totalStock }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <StorefrontPagination
          v-if="filteredRows.length"
          :page="currentPage"
          :page-size="pageSize"
          :size-options="[20, 40, 80]"
          :total-items="filteredRows.length"
          :labels="paginationLabels"
          @update:page="currentPage = $event"
          @update:page-size="pageSize = $event"
        />

        <div v-else class="inventory-state">
          No inventory records match your filters.
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import LazyImage from '../components/LazyImage.vue'
import StorefrontPagination from '../components/StorefrontPagination.vue'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const catalog = useCatalogStore()
const locale = useLocaleStore()

const categoryFilter = ref('')
const keyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const sizeColumns = [
  { key: 'S', label: 'S/28', aliases: ['S', '28'] },
  { key: 'M', label: 'M/30', aliases: ['M', '30'] },
  { key: 'L', label: 'L/32', aliases: ['L', '32'] },
  { key: 'XL', label: 'XL/34', aliases: ['XL', '34'] },
  { key: 'XXL', label: 'XXL/36', aliases: ['XXL', '2XL', '36'] },
  { key: 'XXXL', label: 'XXXL/38', aliases: ['XXXL', '3XL', '38'] },
]

const aliasToColumn = sizeColumns.reduce((map, column) => {
  column.aliases.forEach((alias) => {
    map[String(alias).toUpperCase()] = column.key
  })
  return map
}, {})

const paginationLabels = {
  prev: 'Prev',
  next: 'Next',
  of: 'of',
  perPage: 'Per page',
  itemLabel: 'records',
}

const categoryOptions = computed(() => catalog.categories || [])

const inventoryRows = computed(() =>
  (catalog.products || []).map((product) => {
    const sizeStocks = sizeColumns.reduce((result, column) => {
      result[column.key] = 0
      return result
    }, {})

    ;(product.sizePrices || []).forEach((item) => {
      const normalized = normalizeSizeCode(item.sizeCode)
      const key = aliasToColumn[normalized]
      if (key) {
        sizeStocks[key] += Number(item.stock || 0)
      }
    })

    const summedStock = Object.values(sizeStocks).reduce((sum, value) => sum + Number(value || 0), 0)
    const totalStock = (product.sizePrices || []).length ? summedStock : Number(product.stock || 0)

    return {
      id: product.id,
      slug: product.slug,
      name: product.name || product.productCode || product.sku || 'Untitled Product',
      colorSku: product.productCode || product.sku || '—',
      image: product.image || '',
      colorName: product.colorName || '',
      categoryKey: product.categoryKey || '',
      categoryLabel: englishCategoryLabel(product),
      sizeStocks,
      totalStock,
      searchText: [
        product.name,
        product.productCode,
        product.sku,
        product.colorName,
        product.categoryKey,
        englishCategoryLabel(product),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase(),
    }
  })
)

const filteredRows = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()
  return inventoryRows.value.filter((row) => {
    if (categoryFilter.value && row.categoryKey !== categoryFilter.value) return false
    if (normalizedKeyword && !row.searchText.includes(normalizedKeyword)) return false
    return true
  })
})

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const totalStock = computed(() =>
  filteredRows.value.reduce((sum, row) => sum + Number(row.totalStock || 0), 0)
)

function normalizeSizeCode(value) {
  const raw = String(value || '').trim().toUpperCase().replace(/\s+/g, '')
  if (!raw) return ''
  const parts = raw.split(/[^A-Z0-9]+/).filter(Boolean)
  const candidates = [raw, ...parts]
  return candidates.find((item) => aliasToColumn[item]) || raw
}

function titleCase(value) {
  return String(value || '')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function containsChinese(value) {
  return /[\u3400-\u9fff]/.test(String(value || ''))
}

function englishCategoryLabel(product) {
  const raw = product.categoryLabel || ''
  if (raw && !containsChinese(raw)) return raw
  return titleCase(product.categoryKey || 'Category')
}

async function loadInventory() {
  await catalog.loadHome('en')
  await catalog.loadProducts({}, 'en')
}

watch([categoryFilter, keyword, pageSize], () => {
  currentPage.value = 1
})

watch(
  () => filteredRows.value.length,
  (count) => {
    const totalPages = Math.max(1, Math.ceil(count / pageSize.value))
    if (currentPage.value > totalPages) {
      currentPage.value = totalPages
    }
  }
)

watch(() => locale.current, loadInventory)

onMounted(loadInventory)
</script>

<style scoped>
.inventory-page {
  padding: 36px 0 72px;
}

.inventory-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
  gap: 14px;
  align-items: end;
  margin-bottom: 18px;
}

.inventory-field {
  display: grid;
  gap: 8px;
}

.inventory-field span {
  color: var(--muted);
  font-size: 0.88rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.inventory-field input,
.inventory-field select {
  width: 100%;
  min-height: 50px;
  border: 1px solid var(--line);
  background: #fff;
  padding: 0 16px;
  color: var(--text);
}

.inventory-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.inventory-stat-grid article {
  border: 1px solid var(--line);
  background: #fbf7f2;
  padding: 20px 22px;
}

.inventory-stat-grid span {
  display: block;
  color: var(--muted);
  font-size: 0.88rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.inventory-stat-grid strong {
  display: block;
  margin-top: 8px;
  font-size: clamp(1.5rem, 2.2vw, 2.2rem);
  line-height: 1;
}

.inventory-table-card {
  border: 1px solid var(--line);
  background: #fff;
}

.inventory-table-scroll {
  width: 100%;
  overflow-x: auto;
}

.inventory-table {
  width: 100%;
  min-width: 1180px;
  border-collapse: collapse;
}

.inventory-table th,
.inventory-table td {
  padding: 16px 14px;
  border-bottom: 1px solid var(--line);
  text-align: center;
  vertical-align: middle;
}

.inventory-table th {
  background: #f6efe8;
  color: #111;
  font-size: 0.82rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.inventory-table th:first-child,
.inventory-table td:first-child {
  width: 240px;
  text-align: left;
}

.inventory-product-link {
  display: -webkit-box;
  overflow: hidden;
  font-weight: 800;
  line-height: 1.35;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.inventory-sku {
  font-weight: 800;
  letter-spacing: 0.02em;
}

.inventory-image-link {
  display: inline-block;
}

.inventory-product-image {
  width: 58px;
  border-radius: 14px;
  background: #f3f0ed;
}

.inventory-image-empty {
  display: inline-grid;
  place-items: center;
  width: 58px;
  height: 58px;
  border-radius: 14px;
  background: #f3f0ed;
  color: var(--muted);
  font-size: 0.72rem;
}

.inventory-stock-pill {
  display: inline-flex;
  min-width: 46px;
  justify-content: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: #f4ece6;
  font-weight: 800;
}

.inventory-empty-size {
  color: #b6aea8;
}

.inventory-total {
  color: #b66b3f;
  font-weight: 900;
}

.inventory-state {
  display: grid;
  place-items: center;
  min-height: 180px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--muted);
}

@media (max-width: 900px) {
  .inventory-toolbar,
  .inventory-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
