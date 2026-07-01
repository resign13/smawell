<template>
  <section class="policy-page">
    <div class="container policy-container">
      <RouterLink class="policy-back-link" to="/shop">Back to Store</RouterLink>
      <p class="eyebrow">SMAWELL</p>
      <h1>{{ page.title }}</h1>
      <p class="policy-updated">Last updated: July 1, 2026</p>
      <p class="policy-intro">{{ page.intro }}</p>

      <div class="policy-content">
        <section v-for="section in page.sections" :key="section.heading" class="policy-section">
          <h2>{{ section.heading }}</h2>
          <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
          <ul v-if="section.items?.length">
            <li v-for="item in section.items" :key="item">{{ item }}</li>
          </ul>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const pages = {
  'about-us': {
    title: 'About Us',
    intro: 'SMAWELL is a fashion wholesale and custom order platform created for buyers who need reliable products, clear stock information and efficient order communication.',
    sections: [
      { heading: 'Who We Are', paragraphs: ['We focus on practical fashion categories including womenswear, menswear and everyday wardrobe essentials. Our goal is to make product selection, stock confirmation and order submission easier for international customers.'] },
      { heading: 'What We Provide', paragraphs: ['SMAWELL combines product display, size and color level inventory, online order notes, attachment upload and back-office order handling in one connected workflow.'], items: ['Curated fashion products', 'Color and size based stock visibility', 'Support for custom order notes and reference files', 'Efficient order confirmation and export process'] },
      { heading: 'Our Commitment', paragraphs: ['We aim to provide stable communication, transparent product information and dependable order support so buyers can work with us more confidently.'] },
    ],
  },
  'contact-us': {
    title: 'Contact Us',
    intro: 'If you have questions about products, stock, customization, orders or cooperation, please contact our service team.',
    sections: [
      { heading: 'Business Contact', paragraphs: ['Email: business@smawell.com', 'Phone: +86 20 8888 6688', 'Address: Guangzhou, China'] },
      { heading: 'Order Support', paragraphs: ['For order-related questions, please include your order number, product SKU and a clear description of your request. This helps us check your order faster.'] },
      { heading: 'Response Time', paragraphs: ['We usually respond within 1-2 business days. Response time may be longer during weekends, holidays or peak seasons.'] },
    ],
  },
  'privacy-policy': {
    title: 'Privacy Policy',
    intro: 'This Privacy Policy explains how SMAWELL collects, uses and protects information when you use our website and services.',
    sections: [
      { heading: 'Information We Collect', paragraphs: ['We may collect information you provide during account login, order submission, contact forms and file uploads, including name, company information, email address, shipping information, order notes and attachments.'] },
      { heading: 'How We Use Information', paragraphs: ['We use your information to process orders, confirm products, provide customer support, arrange shipping communication and improve our services.'] },
      { heading: 'Information Protection', paragraphs: ['We apply reasonable technical and organizational measures to protect data. Access to order and customer information is limited to authorized personnel who need it for business operations.'] },
      { heading: 'Third-Party Services', paragraphs: ['We may use third-party hosting, storage, analytics, payment or logistics services where necessary. These services process information only as required to support our business workflow.'] },
      { heading: 'Contact', paragraphs: ['If you have privacy questions, please contact us at business@smawell.com.'] },
    ],
  },
  'terms-of-service': {
    title: 'Terms of Service',
    intro: 'These Terms of Service describe the basic rules for using the SMAWELL website and placing orders through our platform.',
    sections: [
      { heading: 'Use of Website', paragraphs: ['You agree to use this website for lawful business purposes and provide accurate information when submitting inquiries, orders or files.'] },
      { heading: 'Product Information', paragraphs: ['We try to keep product images, descriptions, stock and pricing accurate. However, product availability, colors, packaging and production details may change due to supply conditions.'] },
      { heading: 'Orders', paragraphs: ['An order submitted through the website is a request for confirmation. Final confirmation may depend on stock, customization requirements, shipping cost and payment arrangement.'] },
      { heading: 'Uploaded Content', paragraphs: ['When uploading files or notes, you confirm that the content is relevant to the order and does not violate third-party rights or applicable laws.'] },
      { heading: 'Updates', paragraphs: ['We may update these terms from time to time. Continued use of the website means you accept the latest version.'] },
    ],
  },
  'shipping-policy': {
    title: 'Shipping Policy',
    intro: 'This Shipping Policy explains the general shipping process for orders placed with SMAWELL.',
    sections: [
      { heading: 'Shipping Confirmation', paragraphs: ['Shipping cost and delivery method are confirmed after order details, destination, quantity, package volume and customer requirements are reviewed.'] },
      { heading: 'Processing Time', paragraphs: ['Processing time depends on product availability, order quantity, customization requirements and payment confirmation. We will communicate the estimated schedule after order review.'] },
      { heading: 'Delivery Time', paragraphs: ['Delivery time varies by country, carrier, customs process and shipping method. Any estimated delivery time is for reference only and is not a guaranteed arrival date.'] },
      { heading: 'Customs and Duties', paragraphs: ['Import duties, taxes, customs fees or local charges may be required by the destination country. Unless otherwise agreed, these costs are the responsibility of the buyer.'] },
      { heading: 'Tracking', paragraphs: ['When tracking information is available, we will provide it through the appropriate communication channel or order record.'] },
    ],
  },
  'return-refund-policy': {
    title: 'Return & Refund Policy',
    intro: 'This Return & Refund Policy explains how we handle after-sales requests for confirmed orders.',
    sections: [
      { heading: 'Request Window', paragraphs: ['Please contact us as soon as possible after receiving goods if you find quantity differences, damage, wrong items or other order-related issues.'] },
      { heading: 'Required Evidence', paragraphs: ['To help us review your request, please provide order number, SKU, photos or videos of the issue, package labels and a clear description.'] },
      { heading: 'Customized Products', paragraphs: ['Customized, relabeled or specially produced items may not be eligible for return unless the issue is caused by our confirmed mistake.'] },
      { heading: 'Resolution', paragraphs: ['Depending on the case, we may offer replacement, partial refund, future order credit or another mutually agreed solution.'] },
      { heading: 'Return Shipping', paragraphs: ['Return shipping responsibility depends on the reason for return and the final agreement between both parties.'] },
    ],
  },
  faq: {
    title: 'FAQ',
    intro: 'Here are answers to common questions about SMAWELL products, orders, stock and support.',
    sections: [
      { heading: 'Do I need an account to browse products?', paragraphs: ['No. Product pages can be browsed without forced login. Some order-related features may still require account information for confirmation and support.'] },
      { heading: 'Is the displayed stock accurate?', paragraphs: ['The website displays stock by product color and size where available. Final stock confirmation may still be required before large or customized orders.'] },
      { heading: 'Can I upload notes or reference files when placing an order?', paragraphs: ['Yes. You can submit a text remark and upload reference attachments such as PDF or image files during checkout.'] },
      { heading: 'How is shipping cost confirmed?', paragraphs: ['Shipping cost is calculated after order quantity, destination, package size and preferred shipping method are reviewed.'] },
      { heading: 'Can I request customization?', paragraphs: ['Yes. Please include detailed requirements in the order note or contact us before placing the order.'] },
      { heading: 'Who should I contact for order issues?', paragraphs: ['Please email business@smawell.com with your order number and product SKU so our team can check the details.'] },
    ],
  },
}

const page = computed(() => pages[route.params.slug] || pages['about-us'])
</script>
