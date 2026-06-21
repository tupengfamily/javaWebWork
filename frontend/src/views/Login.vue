<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <h2 class="title">小说数据看板</h2>

      <!-- 模式切换 -->
      <div class="role-tabs" role="tablist">
        <button
          type="button"
          class="role-tab"
          :class="{ active: mode === 'login' }"
          :aria-pressed="mode === 'login'"
          role="tab"
          @click="switchMode('login')"
        >登录</button>
        <button
          type="button"
          class="role-tab"
          :class="{ active: mode === 'register' }"
          :aria-pressed="mode === 'register'"
          role="tab"
          @click="switchMode('register')"
        >注册</button>
      </div>
      <p class="role-desc">
        {{ mode === 'login' ? '已有账号，请输入用户名密码登录' : '新用户注册，注册后自动登录' }}
      </p>

      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="onSubmit">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名（2-32字）"
            :autocomplete="mode === 'login' ? 'username' : 'new-username'"
            :spellcheck="false"
            name="username"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（6-64字）"
            show-password
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            :spellcheck="false"
            name="password"
          />
        </el-form-item>
        <el-form-item v-if="mode === 'register'" prop="password2">
          <el-input
            v-model="form.password2"
            type="password"
            placeholder="确认密码"
            show-password
            autocomplete="new-password"
            :spellcheck="false"
            name="password2"
          />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="submit">
          {{ mode === 'login' ? '登 录' : '注 册' }}
        </el-button>
      </el-form>
      <p class="hint">排行榜和趋势分析无需登录即可查看</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const loading = ref(false)
const mode = ref<'login' | 'register'>('login')

const form = reactive({ username: '', password: '', password2: '' })

const validatePass2 = (_r: any, v: string, cb: any) => {
  if (!v) { cb(new Error('请确认密码')); return }
  if (v !== form.password) { cb(new Error('两次密码不一致')); return }
  cb()
}

const rules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 32, message: '用户名长度 2-32', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64', trigger: 'blur' }
  ],
  password2: [
    { validator: validatePass2, trigger: 'blur' }
  ]
})

const switchMode = (m: 'login' | 'register') => {
  mode.value = m
  form.username = ''
  form.password = ''
  form.password2 = ''
  formRef.value?.clearValidate()
}

const onSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      if (mode.value === 'register') {
        await auth.register(form.username, form.password)
        ElMessage.success('注册成功，已自动登录')
        router.push('/rankings')
      } else {
        await auth.login(form.username, form.password)
        ElMessage.success('登录成功')
        const isAdmin = auth.isAdmin
        const defaultPath = isAdmin ? '/admin/tasks' : '/rankings'
        const redirect = (route.query.redirect as string) || defaultPath
        router.push(redirect)
      }
    } catch {
      // 错误已由拦截器处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px;
  box-sizing: border-box;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 24px 16px;
}

.title {
  text-align: center;
  margin: 0 0 20px;
  color: #303133;
}

.role-tabs {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  margin-bottom: 8px;
}

.role-tab {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  cursor: pointer;
  color: #606266;
  background: #f5f7fa;
  border: 0;                          /* 覆盖 button 默认边框 */
  font-family: inherit;               /* 继承 body 字体 */
  /* 列表具体属性 - 避免 transition: all 带来的性能/可访问性问题 */
  transition: background-color 0.2s, color 0.2s;
  font-size: 14px;
  user-select: none;
}

.role-tab.active {
  background: #409eff;
  color: #fff;
}

.role-tab:first-child {
  border-right: 1px solid #dcdfe6;
}

/* 焦点环 — 让键盘用户能看到当前焦点位置 */
.role-tab:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: -2px;
}

.role-desc {
  text-align: center;
  color: #909399;
  font-size: 12px;
  margin-bottom: 16px;
}

.submit { width: 100%; }

.hint {
  text-align: center;
  color: #909399;
  font-size: 12px;
  margin: 16px 0 0;
}

@media (max-width: 480px) {
  .login-card {
    max-width: 100%;
    padding: 16px 12px;
  }
  .title { font-size: 18px; }
}
</style>
