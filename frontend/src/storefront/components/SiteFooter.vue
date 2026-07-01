<template>
  <footer id="contact" class="site-footer">
    <div class="site-footer-dark">
      <div class="container footer-dark-grid">
        <section class="footer-brand-column">
          <div class="footer-brand-wordmark">{{ locale.t('brand.name') }}</div>
          <p class="footer-column-label">{{ footerCopy.aboutLabel }}</p>
          <p class="footer-brand-text">{{ footerCopy.aboutText }}</p>
        </section>

        <section class="footer-column">
          <p class="footer-column-label">{{ footerCopy.infoLabel }}</p>
          <ul class="footer-link-list">
            <li v-for="item in footerCopy.infoLinks" :key="item.to"><RouterLink :to="item.to">{{ item.label }}</RouterLink></li>
          </ul>
        </section>

        <section class="footer-column">
          <p class="footer-column-label">{{ footerCopy.serviceLabel }}</p>
          <ul class="footer-link-list">
            <li v-for="item in footerCopy.serviceLinks" :key="item.to"><RouterLink :to="item.to">{{ item.label }}</RouterLink></li>
          </ul>
        </section>

        <section class="footer-column footer-contact-column">
          <p class="footer-column-label">{{ footerCopy.contactLabel }}</p>
          <ul class="footer-contact-list">
            <li><span>Email</span><strong>{{ footerCopy.email }}</strong></li>
            <li><span>Phone</span><strong>{{ footerCopy.phone }}</strong></li>
            <li><span>Address</span><strong>{{ footerCopy.address }}</strong></li>
          </ul>
          <RouterLink class="footer-action" to="/shop">
            {{ footerCopy.enter }}
          </RouterLink>
        </section>
      </div>

      <div class="container footer-bottom-bar">
        <p>{{ footerCopy.copyright }}</p>
        <div class="footer-payment-badges">
          <span>Visa</span>
          <span>Mastercard</span>
          <span>Amex</span>
          <span>Apple Pay</span>
          <span>PayPal</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { useLocaleStore } from '../stores/locale'

const locale = useLocaleStore()

const footerCopy = computed(() => ({
  aboutLabel: 'ABOUT US',
  aboutText: 'SMAWELL focuses on womenswear, menswear and fashion essentials with stable stock, premium visuals and a cleaner storefront-to-checkout flow.',
  infoLabel: 'INFORMATION',
  infoLinks: [
    { label: 'About Us', to: '/pages/about-us' },
    { label: 'Contact Us', to: '/pages/contact-us' },
    { label: 'Privacy Policy', to: '/pages/privacy-policy' },
    { label: 'Terms of Service', to: '/pages/terms-of-service' },
  ],
  serviceLabel: 'CUSTOMER SERVICES',
  serviceLinks: [
    { label: 'Shipping Policy', to: '/pages/shipping-policy' },
    { label: 'Return & Refund Policy', to: '/pages/return-refund-policy' },
    { label: 'FAQ', to: '/pages/faq' },
  ],
  contactLabel: 'CONTACT',
  email: 'business@smawell.com',
  phone: '+86 20 8888 6688',
  address: 'Guangzhou, China',
  enter: 'Enter Store',
  copyright: '© 2026 SMAWELL',
}))
</script>
