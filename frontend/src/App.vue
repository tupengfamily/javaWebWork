<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMetaStore } from '@/stores/meta'

const auth = useAuthStore()
const meta = useMetaStore()

onMounted(async () => {
  if (auth.token) {
    await auth.fetchMe().catch(() => {})
  }
  await meta.loadAll().catch(() => {})
})
</script>
