import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/rankings',
    children: [
      {
        path: 'rankings',
        name: 'rankings',
        component: () => import('@/views/Rankings.vue'),
        meta: { title: '排行榜', public: true }
      },
      {
        path: 'novels/:id(\\d+)',
        name: 'novel-detail',
        component: () => import('@/views/NovelDetail.vue'),
        meta: { title: '小说详情', requiresAuth: true }
      },
      {
        path: 'trends',
        name: 'trends',
        component: () => import('@/views/Trends.vue'),
        meta: { title: '趋势分析', public: true }
      },
      {
        path: 'admin/tasks',
        name: 'admin-tasks',
        component: () => import('@/views/admin/Tasks.vue'),
        meta: { title: '任务管理', requiresAdmin: true }
      },
      {
        path: 'admin/data',
        name: 'admin-data',
        component: () => import('@/views/admin/CrawlerData.vue'),
        meta: { title: '数据管理', requiresAdmin: true }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/rankings' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  // 公开页面无需登录
  if (to.meta.public) return true
  // 需要登录的页面
  if (to.meta.requiresAuth || to.meta.requiresAdmin) {
    if (!auth.isLogin) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
    // admin 验证：等 user 加载完成后再判断，避免刷新时误判
    if (to.meta.requiresAdmin && auth.isReady && !auth.isAdmin) {
      return { path: '/rankings' }
    }
  }
  return true
})

export default router
