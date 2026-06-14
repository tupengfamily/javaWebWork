<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="logo">📚 小说数据看板</div>
      <el-menu mode="horizontal" :default-active="activeMenu" :router="false" @select="onSelect" class="menu">
        <el-menu-item index="/rankings">排行榜</el-menu-item>
        <el-menu-item index="/trends">趋势分析</el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/admin/tasks">任务管理</el-menu-item>
      </el-menu>
      <div class="user-area">
        <template v-if="auth.isLogin">
          <el-dropdown @command="onCommand">
            <span class="user-name">{{ auth.user?.username || '用户' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click="$router.push('/login')">登录</el-button>
        </template>
      </div>
    </el-header>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin')) return '/admin/tasks'
  if (route.path.startsWith('/trends')) return '/trends'
  return '/rankings'
})

const onSelect = (index: string) => router.push(index)

const onCommand = async (cmd: string) => {
  if (cmd === 'logout') {
    await auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout { min-height: 100vh; }
.header {
  display: flex; align-items: center;
  background: #fff; border-bottom: 1px solid #ebeef5;
  padding: 0 24px;
}
.logo { font-size: 18px; font-weight: bold; margin-right: 32px; color: #409eff; }
.menu { flex: 1; border-bottom: none; }
.user-area { margin-left: auto; }
.user-name { cursor: pointer; display: inline-flex; align-items: center; gap: 4px; }
.main { background: #f5f7fa; padding: 24px; }
</style>
