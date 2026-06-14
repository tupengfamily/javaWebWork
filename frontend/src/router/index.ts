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
        meta: { title: '排行榜' }
      },
      {
        path: 'novels/:id(\\d+)',
        name: 'novel-detail',
        component: () => import('@/views/NovelDetail.vue'),
        meta: { title: '小说详情' }
      },
      {
        path: 'trends',
        name: 'trends',
        component: () => import('@/views/Trends.vue'),
        meta: { title: '趋势分析' }
      },
      {
        path: 'admin/tasks',
        name: 'admin-tasks',
        component: () => import('@/views/admin/Tasks.vue'),
        meta: { title: '任务管理', requiresAdmin: true }
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
  if (to.meta.public) return true
  if (!auth.isLogin) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { path: '/rankings' }
  }
  return true
})

export default router
