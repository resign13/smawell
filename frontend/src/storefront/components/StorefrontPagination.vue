<template>
  <div v-if="totalItems > 0" class="store-pager">
    <div class="store-pager-meta">
      <strong>{{ startItem }}-{{ endItem }}</strong>
      <span>{{ labels.of }} {{ totalItems }} {{ labels.itemLabel }}</span>
    </div>

    <div class="store-pager-controls">
      <label class="store-pager-size">
        <span>{{ labels.perPage }}</span>
        <select :value="pageSize" @change="handlePageSizeChange">
          <option v-for="option in sizeOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </label>

      <div class="store-pager-buttons">
        <button
          class="store-pager-button"
          type="button"
          :disabled="page <= 1"
          @click="setPage(page - 1)"
        >
          {{ labels.prev }}
        </button>

        <button
          v-for="pageNumber in visiblePages"
          :key="pageNumber"
          :class="['store-pager-button', { active: pageNumber === page }]"
          type="button"
          @click="setPage(pageNumber)"
        >
          {{ pageNumber }}
        </button>

        <button
          class="store-pager-button"
          type="button"
          :disabled="page >= totalPages"
          @click="setPage(page + 1)"
        >
          {{ labels.next }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: {
    type: Number,
    required: true,
  },
  pageSize: {
    type: Number,
    required: true,
  },
  totalItems: {
    type: Number,
    required: true,
  },
  sizeOptions: {
    type: Array,
    default: () => [12, 24, 36],
  },
  labels: {
    type: Object,
    default: () => ({
      prev: 'Prev',
      next: 'Next',
      of: 'of',
      perPage: 'Per page',
      itemLabel: 'products',
    }),
  },
})

const emit = defineEmits(['update:page', 'update:pageSize'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalItems / props.pageSize)))
const safePage = computed(() => Math.min(Math.max(1, props.page), totalPages.value))
const startItem = computed(() => {
  if (!props.totalItems) return 0
  return (safePage.value - 1) * props.pageSize + 1
})
const endItem = computed(() => Math.min(props.totalItems, safePage.value * props.pageSize))
const visiblePages = computed(() => {
  const start = Math.max(1, safePage.value - 2)
  const end = Math.min(totalPages.value, start + 4)
  const pages = []
  for (let pageNumber = Math.max(1, end - 4); pageNumber <= end; pageNumber += 1) {
    pages.push(pageNumber)
  }
  return pages
})

function setPage(nextPage) {
  emit('update:page', Math.min(Math.max(1, nextPage), totalPages.value))
}

function handlePageSizeChange(event) {
  emit('update:pageSize', Number(event.target.value || props.pageSize))
  emit('update:page', 1)
}
</script>

<style scoped>
.store-pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-top: 30px;
  padding-top: 26px;
  border-top: 1px solid rgba(17, 17, 17, 0.08);
}

.store-pager-meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: var(--muted);
}

.store-pager-controls,
.store-pager-buttons,
.store-pager-size {
  display: flex;
  align-items: center;
  gap: 12px;
}

.store-pager-size span {
  color: var(--muted);
  font-size: 0.92rem;
}

.store-pager-size select {
  min-height: 42px;
  border: 1px solid var(--line);
  background: #fff;
  padding: 0 12px;
}

.store-pager-button {
  min-width: 42px;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid var(--line);
  background: #fff;
  cursor: pointer;
}

.store-pager-button.active {
  border-color: #111;
  background: #111;
  color: #fff;
}

.store-pager-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .store-pager,
  .store-pager-controls {
    flex-direction: column;
    align-items: flex-start;
  }

  .store-pager-buttons {
    flex-wrap: wrap;
  }
}
</style>
