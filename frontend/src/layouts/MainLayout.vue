<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="logo">📚 小说数据看板</div>
      <el-menu
        mode="horizontal"
        :default-active="activeMenu"
        :router="false"
        @select="onSelect"
        class="menu"
        :collapse="false"
      >
        <el-menu-item index="/rankings">排行榜</el-menu-item>
        <el-menu-item index="/trends">趋势分析</el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/admin/tasks">任务管理</el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/admin/data">数据管理</el-menu-item>
      </el-menu>
      <div class="user-area">
        <template v-if="auth.isLogin">
          <el-dropdown @command="onCommand">
            <span class="user-name">{{ auth.user?.username || '用户' }}
              <el-tag v-if="auth.isAdmin" size="small" type="danger" effect="plain">管理</el-tag>
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
  if (route.path.startsWith('/admin/data')) return '/admin/data'
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
.layout {
  height: 100vh;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  padding: 0 24px;
  white-space: nowrap;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  margin-right: 24px;
  color: #409eff;
  flex-shrink: 0;
}

.menu {
  flex: 1;
  border-bottom: none;
  min-width: 0;
}

.user-area {
  margin-left: auto;
  flex-shrink: 0;
}

.user-name {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.main {
  background: #f5f7fa;
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 笔记本 / 小屏幕 */
@media (max-width: 992px) {
  .header {
    padding: 0 16px;
  }
  .logo {
    font-size: 15px;
    margin-right: 12px;
  }
  .main {
    padding: 12px;
  }
}

/* 平板 */
@media (max-width: 768px) {
  .header {
    padding: 0 12px;
    flex-wrap: wrap;
    height: auto;
    padding-top: 8px;
    padding-bottom: 8px;
  }
  .logo {
    font-size: 14px;
    margin-right: auto;
  }
  .menu {
    order: 3;
    width: 100%;
  }
  .user-area {
    margin-left: 0;
  }
  .main {
    padding: 8px;
  }
}

/* 手机 */
@media (max-width: 576px) {
  .header {
    padding: 8px;
  }
  .logo {
    font-size: 13px;
  }
  :deep(.el-menu--horizontal) > .el-menu-item {
    padding: 0 10px;
    font-size: 13px;
  }
  .main {
    padding: 8px;
  }
}
</style>
