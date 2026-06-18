import { createApp } from 'vue'

import AppShell from './storefront/AppShell.vue'
import router from './storefront/router'
import { pinia } from './storefront/stores'
import './storefront/styles.css'

const app = createApp(AppShell)

app.use(pinia)
app.use(router)
app.mount('#app')
