import { defineStore } from 'pinia'

import { translations } from '../translations'

const STORAGE_KEY = 'smawell-locale'

function getByPath(source, path) {
  return path.split('.').reduce((result, key) => result?.[key], source)
}

export const useLocaleStore = defineStore('locale', {
  state: () => ({
    current: 'en',
    supported: [{ code: 'en', label: 'EN' }],
  }),
  actions: {
    setLanguage() {
      this.current = 'en'
      try {
        localStorage.setItem(STORAGE_KEY, 'en')
      } catch {
        // ignore storage errors
      }
    },
    t(path) {
      return getByPath(translations.en, path) ?? path
    },
  },
})
