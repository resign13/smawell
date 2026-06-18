<template>
  <section class="checkout-page">
    <div class="container">
      <div v-if="!cart.items.length" class="panel-card empty-state-card">
        <p class="eyebrow">{{ checkoutCopy.title }}</p>
        <h1>{{ locale.t('common.emptyCart') }}</h1>
        <p class="helper">{{ checkoutCopy.empty }}</p>
        <RouterLink class="primary-button inline-button" to="/shop">
          {{ locale.t('common.continueShopping') }}
        </RouterLink>
      </div>

      <form v-else class="checkout-layout" @submit.prevent="handleSubmit">
        <section class="panel-card checkout-form-card">
          <div class="section-stack">
            <div class="checkout-section">
              <div class="checkout-section-head">
                <h2>{{ checkoutCopy.contactTitle }}</h2>
              </div>

              <div class="checkout-grid">
                <div>
                  <input
                    v-model.trim="form.email"
                    class="field"
                    :class="{ 'field-error': errors.email }"
                    :placeholder="checkoutCopy.emailPlaceholder"
                    @blur="validateField('email')"
                    @input="clearContactErrors"
                  />
                  <p v-if="errors.email" class="field-error-text">{{ errors.email }}</p>
                </div>

                <div>
                  <input
                    v-model.trim="form.phone"
                    class="field"
                    :class="{ 'field-error': errors.phone }"
                    :placeholder="checkoutCopy.phonePlaceholder"
                    @blur="validateField('phone')"
                    @input="clearContactErrors"
                  />
                  <p v-if="errors.phone" class="field-error-text">{{ errors.phone }}</p>
                </div>
              </div>
            </div>

            <div class="checkout-section">
              <div class="checkout-section-head">
                <h2>{{ checkoutCopy.deliveryTitle }}</h2>
              </div>

              <div class="checkout-grid">
                <div class="checkout-grid-span">
                  <select
                    v-model="form.country"
                    class="field checkout-select"
                    :class="{ 'field-error': errors.country }"
                    @change="validateField('country')"
                  >
                    <option value="">{{ checkoutCopy.countryPlaceholder }}</option>
                    <option v-for="item in countryOptions" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                  <p v-if="errors.country" class="field-error-text">{{ errors.country }}</p>
                </div>

                <div>
                  <input
                    v-model.trim="form.firstName"
                    class="field"
                    :placeholder="checkoutCopy.firstNamePlaceholder"
                  />
                </div>

                <div>
                  <input
                    v-model.trim="form.lastName"
                    class="field"
                    :class="{ 'field-error': errors.lastName }"
                    :placeholder="checkoutCopy.lastNamePlaceholder"
                    @blur="validateField('lastName')"
                    @input="clearFieldError('lastName')"
                  />
                  <p v-if="errors.lastName" class="field-error-text">{{ errors.lastName }}</p>
                </div>

                <div class="checkout-grid-span">
                  <input
                    v-model.trim="form.address"
                    class="field"
                    :class="{ 'field-error': errors.address }"
                    :placeholder="checkoutCopy.addressPlaceholder"
                    @blur="validateField('address')"
                    @input="clearFieldError('address')"
                  />
                  <p v-if="errors.address" class="field-error-text">{{ errors.address }}</p>
                </div>

                <div class="checkout-grid-span">
                  <input
                    v-model.trim="form.apartment"
                    class="field"
                    :placeholder="checkoutCopy.apartmentPlaceholder"
                  />
                </div>

                <div>
                  <input
                    v-model.trim="form.city"
                    class="field"
                    :class="{ 'field-error': errors.city }"
                    :placeholder="checkoutCopy.cityPlaceholder"
                    @blur="validateField('city')"
                    @input="clearFieldError('city')"
                  />
                  <p v-if="errors.city" class="field-error-text">{{ errors.city }}</p>
                </div>

                <div>
                  <input
                    v-model.trim="form.state"
                    class="field"
                    :class="{ 'field-error': errors.state }"
                    :placeholder="checkoutCopy.statePlaceholder"
                    @blur="validateField('state')"
                    @input="clearFieldError('state')"
                  />
                  <p v-if="errors.state" class="field-error-text">{{ errors.state }}</p>
                </div>

                <div class="checkout-grid-span">
                  <input
                    v-model.trim="form.zip"
                    class="field"
                    :class="{ 'field-error': errors.zip }"
                    :placeholder="checkoutCopy.zipPlaceholder"
                    @blur="validateField('zip')"
                    @input="clearFieldError('zip')"
                  />
                  <p v-if="errors.zip" class="field-error-text">{{ errors.zip }}</p>
                </div>
              </div>
            </div>

            <div class="checkout-section checkout-smart-parser">
              <div class="checkout-section-head">
                <h2>{{ checkoutCopy.smartAddressTitle }}</h2>
              </div>

              <div class="checkout-stack">
                <textarea
                  v-model.trim="addressPaste"
                  class="field textarea"
                  :placeholder="checkoutCopy.smartAddressPlaceholder"
                  @input="clearAddressParseMessages"
                />

                <div class="checkout-smart-actions">
                  <button class="secondary-button inline-button" type="button" @click="parseSmartAddress">
                    {{ checkoutCopy.parseAddress }}
                  </button>
                  <span v-if="addressParseMessage" class="helper">{{ addressParseMessage }}</span>
                </div>
              </div>
            </div>

            <div class="checkout-section">
              <div class="checkout-section-head">
                <h2>{{ checkoutCopy.customizationTitle }}</h2>
              </div>

              <div class="checkout-stack">
                <textarea
                  v-model.trim="form.note"
                  class="field textarea"
                  :placeholder="checkoutCopy.notePlaceholder"
                />

                <div class="checkout-upload-row">
                  <input
                    id="checkout-attachment-input"
                    ref="attachmentInput"
                    class="checkout-file-input"
                    type="file"
                    accept="application/pdf,image/jpeg,image/png,image/webp,.pdf,.jpg,.jpeg,.png,.webp"
                    multiple
                    :disabled="uploadingAttachment || form.labelImages.length >= 5"
                    @change="handleAttachmentChange"
                  />
                  <div class="checkout-upload-card">
                    <button
                      type="button"
                      class="secondary-button checkout-upload-trigger"
                      :disabled="uploadingAttachment || form.labelImages.length >= 5"
                      @click="openAttachmentPicker"
                    >
                      {{
                        uploadingAttachment
                          ? checkoutCopy.uploadingAttachmentShort
                          : checkoutCopy.selectAttachments
                      }}
                    </button>

                    <div class="checkout-upload-copy">
                      <strong>
                        {{
                          form.labelImages.length
                            ? `${checkoutCopy.uploadedAttachment} ${form.labelImages.length}/5`
                            : checkoutCopy.attachmentTitle
                        }}
                      </strong>
                      <span class="helper">{{ checkoutCopy.attachmentHelp }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="form.labelImages.length" class="checkout-attachment-list">
                  <article v-for="(image, index) in form.labelImages" :key="image.url" class="checkout-attachment-item">
                    <a :href="image.url" target="_blank" rel="noreferrer" class="checkout-attachment-link">
                      <img
                        v-if="isImageAttachment(image.url)"
                        :src="image.url"
                        :alt="image.filename || `Attachment ${index + 1}`"
                      />
                      <div v-else class="checkout-attachment-file">PDF</div>
                    </a>
                    <span>{{ image.filename || `Attachment ${index + 1}` }}</span>
                    <button type="button" class="text-button" @click="removeAttachment(index)">
                      {{ checkoutCopy.removeAttachment }}
                    </button>
                  </article>
                </div>
              </div>
            </div>

            <p v-if="catalog.error" class="error-text">{{ catalog.error }}</p>
            <p v-if="successMessage" class="success-text">{{ successMessage }}</p>

            <button class="primary-button" type="submit" :disabled="submitting">
              {{ submitting ? locale.t('common.loading') : checkoutCopy.submit }}
            </button>
          </div>
        </section>

        <aside class="panel-card checkout-summary-card">
          <div class="checkout-summary-head">
            <h2>{{ checkoutCopy.summaryTitle }}</h2>
          </div>

          <div class="checkout-item-list">
            <article v-for="item in cart.items" :key="item.lineKey" class="checkout-item">
              <img :src="item.image" :alt="item.name" />
              <div class="checkout-item-copy">
                <strong>{{ item.name }}</strong>
                <p>SKU {{ item.sku }}</p>
                <p v-if="item.sizeCode">{{ checkoutCopy.sizeLabel }} {{ item.sizeCode }}</p>
                <span>{{ item.formattedUnitPrice }} x {{ item.quantity }}</span>
                <small>{{ locale.t('common.total') }}: {{ item.formattedLineTotal }}</small>
              </div>
              <div class="checkout-item-actions">
                <input
                  class="field quantity-field"
                  type="number"
                  min="1"
                  :max="item.stock"
                  :value="item.quantity"
                  @input="cart.updateQuantity(item.lineKey, Number($event.target.value || 1))"
                />
                <button class="text-button" type="button" @click="cart.removeItem(item.lineKey)">
                  {{ locale.t('common.remove') }}
                </button>
              </div>
            </article>
          </div>

          <div class="checkout-total-row">
            <span>{{ locale.t('common.subtotal') }}</span>
            <strong>{{ formattedSubtotal }}</strong>
          </div>
          <div class="checkout-total-row checkout-total-strong">
            <span>{{ locale.t('common.total') }}</span>
            <strong>{{ formattedSubtotal }}</strong>
          </div>
        </aside>
      </form>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'
import { useCatalogStore } from '../stores/catalog'
import { useLocaleStore } from '../stores/locale'

const auth = useAuthStore()
const cart = useCartStore()
const catalog = useCatalogStore()
const locale = useLocaleStore()
const router = useRouter()
const attachmentInput = ref(null)

const checkoutCopy = computed(() => ({
  title: 'Checkout',
  contactTitle: 'Contact',
  emailPlaceholder: 'Email (optional if phone is filled)',
  phonePlaceholder: 'Phone number (optional if email is filled)',
  deliveryTitle: 'Delivery Address',
  smartAddressTitle: 'Smart Address Fill',
  smartAddressPlaceholder:
    "Paste a full address, for example: Yacine Belkedrouci, 7 Avenue de l'Appel du 18 Juin 1940, Appt A22, 77100 Meaux, France",
  parseAddress: 'Auto Fill Address',
  parseAddressSuccess: 'The address has been split into the fields above.',
  parseAddressFailed: 'We could not fully parse this address. Please adjust the fields manually.',
  countryPlaceholder: 'Country / Region',
  firstNamePlaceholder: 'First name (optional)',
  lastNamePlaceholder: 'Last name',
  addressPlaceholder: 'Address',
  apartmentPlaceholder: 'Apartment, suite, etc. (optional)',
  cityPlaceholder: 'City',
  statePlaceholder: 'State / Province / Region',
  zipPlaceholder: 'ZIP / Postal code',
  customizationTitle: 'Order Note & Attachments',
  notePlaceholder: 'Add a note for this order (optional)',
  attachmentTitle: 'Upload reference files',
  attachmentHelp: 'Optional. Upload up to 5 PDF/JPG/PNG/WebP files, max 10MB each.',
  selectAttachments: 'Choose Files',
  uploadingAttachment: 'Uploading attachments...',
  uploadingAttachmentShort: 'Uploading...',
  uploadedAttachment: 'Uploaded files:',
  removeAttachment: 'Remove',
  submit: 'Submit Order',
  success: 'Order submitted successfully. You can review it in your account.',
  empty: 'Please add products to your cart before checkout.',
  summaryTitle: 'Order Summary',
  sizeLabel: 'Size',
  errors: {
    contactRequired: 'Please enter either an email or a phone number',
    emailFormat: 'Please enter a valid email address',
    phoneFormat: 'Please enter a valid phone number',
    country: 'Please select a country or region',
    lastName: 'Please enter your last name',
    address: 'Please enter the address',
    city: 'Please enter the city',
    state: 'Please enter the state, province, or region',
    zip: 'Please enter the ZIP or postal code',
    zipFormat: 'Please enter a valid ZIP or postal code',
  },
}))

const countryOptions = computed(() => [
  { value: 'China', label: 'China' },
  { value: 'United States', label: 'United States' },
  { value: 'France', label: 'France' },
  { value: 'United Kingdom', label: 'United Kingdom' },
  { value: 'Canada', label: 'Canada' },
  { value: 'Germany', label: 'Germany' },
  { value: 'Australia', label: 'Australia' },
])

const REGION_HINTS = {
  France: 'Ile-de-France',
}

const submitting = ref(false)
const uploadingAttachment = ref(false)
const successMessage = ref('')
const addressPaste = ref('')
const addressParseMessage = ref('')
const errors = reactive({
  email: '',
  phone: '',
  country: '',
  lastName: '',
  address: '',
  city: '',
  state: '',
  zip: '',
})

const form = reactive({
  email: auth.user?.email || '',
  marketingOptIn: false,
  country: '',
  firstName: auth.user?.name?.split(' ')[0] || '',
  lastName: auth.user?.name?.split(' ').slice(1).join(' ') || '',
  address: '',
  apartment: '',
  city: '',
  state: '',
  zip: '',
  phone: '',
  note: '',
  labelImages: [],
})


const formattedSubtotal = computed(() =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(cart.subtotal)
)

function clearFieldError(field) {
  errors[field] = ''
}

function clearContactErrors() {
  errors.email = ''
  errors.phone = ''
}

function clearAddressParseMessages() {
  addressParseMessage.value = ''
}

function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

function isPhone(value) {
  return /^[0-9+\-\s()]{6,}$/.test(value)
}

function normalizeCountryValue(value) {
  const normalized = String(value || '').trim().toLowerCase()
  const match = countryOptions.value.find((item) => item.value.toLowerCase() == normalized)
  return match?.value || value.trim()
}

function guessRegion(country, zip) {
  if (country === 'France') {
    return REGION_HINTS.France
  }
  return ''
}

function validateContactFields() {
  const email = form.email.trim()
  const phone = form.phone.trim()

  clearContactErrors()

  if (!email && !phone) {
    errors.email = checkoutCopy.value.errors.contactRequired
    errors.phone = checkoutCopy.value.errors.contactRequired
    return false
  }

  if (email && !isEmail(email)) {
    errors.email = checkoutCopy.value.errors.emailFormat
  }

  if (phone && !isPhone(phone)) {
    errors.phone = checkoutCopy.value.errors.phoneFormat
  }

  return !errors.email && !errors.phone
}

function validateField(field) {
  const value = String(form[field] || '').trim()

  if (field === 'email' || field === 'phone') {
    return validateContactFields()
  }
  if (field === 'country') {
    errors.country = value ? '' : checkoutCopy.value.errors.country
    return !errors.country
  }
  if (field === 'lastName') {
    errors.lastName = value ? '' : checkoutCopy.value.errors.lastName
    return !errors.lastName
  }
  if (field === 'address') {
    errors.address = value ? '' : checkoutCopy.value.errors.address
    return !errors.address
  }
  if (field === 'city') {
    errors.city = value ? '' : checkoutCopy.value.errors.city
    return !errors.city
  }
  if (field === 'state') {
    errors.state = value ? '' : checkoutCopy.value.errors.state
    return !errors.state
  }
  if (field === 'zip') {
    if (!value) {
      errors.zip = checkoutCopy.value.errors.zip
      return false
    }
    if (!/^[A-Za-z0-9 -]{3,12}$/.test(value)) {
      errors.zip = checkoutCopy.value.errors.zipFormat
      return false
    }
    errors.zip = ''
    return true
  }
  return true
}

function validateForm() {
  const fields = ['email', 'phone', 'country', 'lastName', 'address', 'city', 'state', 'zip']
  return fields.every((field) => validateField(field))
}

function parseZipAndCity(value) {
  const zipFirst = value.match(/^([A-Za-z0-9-]{3,12})\s+(.+)$/)
  if (zipFirst) {
    return {
      zip: zipFirst[1].trim(),
      city: zipFirst[2].trim(),
    }
  }

  const cityFirst = value.match(/^(.+?)\s+([A-Za-z0-9-]{3,12})$/)
  if (cityFirst) {
    return {
      city: cityFirst[1].trim(),
      zip: cityFirst[2].trim(),
    }
  }

  return {
    city: value.trim(),
    zip: '',
  }
}

function parseSmartAddress() {
  const source = addressPaste.value.trim()
  if (!source) {
    addressParseMessage.value = checkoutCopy.value.parseAddressFailed
    return
  }

  const parts = source
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

  if (parts.length < 4) {
    addressParseMessage.value = checkoutCopy.value.parseAddressFailed
    return
  }

  const fullName = parts[0]
  const country = normalizeCountryValue(parts[parts.length - 1] || '')
  const zipCityRaw = parts[parts.length - 2] || ''
  const middleParts = parts.slice(1, -2)
  const apartmentIndex = middleParts.findIndex((item) =>
    /^(apt|appt|apartment|suite|unit|room|floor|#)/i.test(item)
  )
  const apartment = apartmentIndex >= 0 ? middleParts[apartmentIndex] : ''
  const addressParts = middleParts.filter((_, index) => index !== apartmentIndex)
  const address = addressParts.join(', ')
  const { city, zip } = parseZipAndCity(zipCityRaw)

  const nameParts = fullName.split(/\s+/).filter(Boolean)
  const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : fullName
  const firstName = nameParts.length > 1 ? nameParts.slice(0, -1).join(' ') : ''

  form.firstName = firstName
  form.lastName = lastName
  form.address = address || form.address
  form.apartment = apartment || form.apartment
  form.city = city || form.city
  form.zip = zip || form.zip
  form.country = country || form.country
  form.state = guessRegion(country, zip) || form.state

  clearFieldError('country')
  clearFieldError('lastName')
  clearFieldError('address')
  clearFieldError('city')
  clearFieldError('state')
  clearFieldError('zip')
  addressParseMessage.value = checkoutCopy.value.parseAddressSuccess
}

async function handleAttachmentChange(event) {
  const files = Array.from(event?.target?.files || [])
  if (!files.length) return
  const remaining = 5 - form.labelImages.length
  if (remaining <= 0) {
    window.alert('You can upload up to 5 attachments')
    if (attachmentInput.value) attachmentInput.value.value = ''
    return
  }
  const selected = files.slice(0, remaining)
  if (files.length > remaining) {
    window.alert('You can upload up to 5 attachments')
  }
  if (selected.some((file) => !/\.(pdf|jpe?g|png|webp)$/i.test(file.name))) {
    window.alert('Only PDF, JPG, PNG, or WebP files are supported')
    if (attachmentInput.value) attachmentInput.value.value = ''
    return
  }
  uploadingAttachment.value = true
  catalog.clearMessages()
  try {
    const result = await catalog.uploadOrderAttachment(selected)
    const uploaded = Array.isArray(result?.items)
      ? result.items
      : result?.url
        ? [{ url: result.url, filename: result.filename || selected[0]?.name || '' }]
        : []
    uploaded.forEach((item) => {
      if (item?.url && form.labelImages.length < 5) {
        form.labelImages.push({ url: item.url, filename: item.filename || '' })
      }
    })
  } finally {
    uploadingAttachment.value = false
    if (attachmentInput.value) attachmentInput.value.value = ''
  }
}

function removeAttachment(index) {
  form.labelImages.splice(index, 1)
}

function openAttachmentPicker() {
  if (uploadingAttachment.value || form.labelImages.length >= 5) return
  attachmentInput.value?.click()
}

function isImageAttachment(url) {
  return /\.(jpe?g|png|webp)(?:$|[?#])/i.test(String(url || ""))
}

async function handleSubmit() {
  if (!cart.items.length || !validateForm()) return

  submitting.value = true
  successMessage.value = ''
  catalog.clearMessages()

  try {
    const order = await catalog.createOrder({
      contact: {
        value: form.email,
        marketingOptIn: form.marketingOptIn,
      },
      delivery: {
        country: form.country,
        firstName: form.firstName,
        lastName: form.lastName,
        address: form.address,
        apartment: form.apartment,
        city: form.city,
        state: form.state,
        zip: form.zip,
        phone: form.phone,
      },
      items: cart.items.map((item) => ({
        productId: item.id,
        sizeCode: item.sizeCode,
        quantity: item.quantity,
      })),
      note: form.note,
      labelImageUrls: form.labelImages.map((image) => image.url),
    })

    if (!order) return

    cart.clear()
    successMessage.value = checkoutCopy.value.success
    router.push('/shop')
  } finally {
    submitting.value = false
  }
}
</script>
