<template>
  <div class="page">
    <h2>任务管理</h2>
    <p class="now">当前时间: {{ now }}</p>

    <!-- 1. 站点状态 -->
    <el-card class="block">
      <h3>站点状态</h3>
      <el-row :gutter="12">
        <el-col v-for="s in siteStatus" :key="s.siteId" :span="8">
          <el-card class="site-card" :body-style="{ padding: '12px' }">
            <div class="site-head">
              <el-tag :color="s.color" effect="dark" style="color: #fff; border-color: transparent">{{ s.siteName }}</el-tag>
              <el-tag :type="s.enabled ? 'success' : 'info'" size="small">{{ s.enabled ? '启用' : '禁用' }}</el-tag>
            </div>
            <p class="mt">共 {{ s.novelCount }} 本小说</p>
            <p v-if="s.lastTask">
              上次:
              <el-tag size="small" :type="statusType(s.lastTask.status)">{{ s.lastTask.status }}</el-tag>
              {{ s.lastTask.finishedAt }}
            </p>
            <p v-else>尚无任务</p>
            <p v-if="s.recentFailureCount > 0" class="warn">近 7 天失败 {{ s.recentFailureCount }} 次</p>
            <el-button size="small" type="primary" @click="triggerSite(s.siteCode)">手动触发</el-button>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 2. 调度配置 -->
    <el-card class="block">
      <h3>调度配置</h3>
      <div v-if="schedule">
        <div class="time-row">
          <el-tag v-for="(t, idx) in schedule.dailyCrawlTimes" :key="idx" closable @close="removeTime(idx)">{{ t }}</el-tag>
          <el-input v-if="adding" v-model="newTime" placeholder="HH:mm" style="width: 100px" @keyup.enter="addTime" @blur="addTime" />
          <el-button v-else size="small" @click="adding = true; newTime = ''">+ 添加</el-button>
        </div>
        <el-form :inline="true" class="mt">
          <el-form-item label="最大并发">
            <el-input-number v-model="schedule.maxConcurrentTasks" :min="1" :max="10" />
          </el-form-item>
          <el-form-item label="超时(分钟)">
            <el-input-number v-model="schedule.taskTimeoutMinutes" :min="5" :max="240" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSchedule">保存</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 3. 任务列表 -->
    <el-card class="block">
      <div class="row-between">
        <h3>任务列表</h3>
        <el-select v-model="taskFilter.status" placeholder="状态" clearable @change="fetchTasks" style="width: 140px">
          <el-option label="待执行" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </div>
      <el-table :data="taskData.records" v-loading="taskLoading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="siteName" label="站点" width="100" />
        <el-table-column prop="rankingType" label="榜单" width="100" />
        <el-table-column prop="triggerType" label="触发" width="100" />
        <el-table-column prop="fetchedCount" label="抓取" width="80" align="right" />
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column prop="finishedAt" label="完成时间" width="180" />
        <el-table-column label="耗时" width="90">
          <template #default="{ row }">{{ row.durationMs ? Math.round(row.durationMs / 1000) + 's' : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" size="small" @click="cancelTask(row.id)">取消</el-button>
            <el-button v-if="row.status === 'failed'" size="small" type="primary" @click="retryTask(row.id)">重试</el-button>
            <el-button size="small" @click="viewLog(row.id)">日志</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        background layout="total, prev, pager, next, jumper"
        :total="taskData.total" :current-page="taskFilter.pageNum"
        @current-change="(p) => { taskFilter.pageNum = p; fetchTasks() }"
        class="pager"
      />
    </el-card>

    <!-- 4. 实时日志 -->
    <el-card class="block">
      <div class="row-between">
        <h3>实时日志</h3>
        <div>
          <el-select v-model="logFilter.level" placeholder="级别" clearable @change="fetchLogs" style="width: 120px">
            <el-option label="INFO" value="INFO" />
            <el-option label="WARN" value="WARN" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
        </div>
      </div>
      <div class="log-stream">
        <div v-for="(l, i) in logs" :key="i" class="log-line" :class="logLevelClass(l.level)">
          <span class="time">{{ l.time }}</span>
          <span class="level">[{{ l.level }}]</span>
          <span v-if="l.site" class="site">{{ l.site }}</span>
          <span class="msg">{{ l.message }}</span>
        </div>
        <el-empty v-if="!logs.length" description="暂无日志" :image-size="60" />
      </div>
    </el-card>

    <!-- 手动触发弹窗 -->
    <el-dialog v-model="triggerDialog.visible" title="手动触发爬虫" width="420px">
      <el-form :model="triggerDialog.form">
        <el-form-item label="站点">
          <el-select v-model="triggerDialog.form.siteCode">
            <el-option v-for="s in siteStatus" :key="s.siteCode" :label="s.siteName" :value="s.siteCode" />
          </el-select>
        </el-form-item>
        <el-form-item label="榜单类型">
          <el-select v-model="triggerDialog.form.rankingType">
            <el-option v-for="t in useMetaStore().rankingTypes" :key="t.code" :label="t.name" :value="t.code" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="triggerDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="triggerDialog.loading" @click="confirmTrigger">触发</el-button>
      </template>
    </el-dialog>

    <!-- 任务日志弹窗 -->
    <el-dialog v-model="logDialog.visible" :title="`任务 #${logDialog.taskId} 日志`" width="640px">
      <el-table :data="logDialog.logs" max-height="400">
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="statusType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  listTasks, createTask, cancelTask as apiCancelTask, retryTask as apiRetryTask, getTaskLog,
  listDashboardLogs, dashboardSites, type TaskVO
} from '@/api/tasks'
import { getSchedule, updateSchedule, type ScheduleConfig } from '@/api/schedule'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const now = ref(dayjs().format('YYYY-MM-DD HH:mm:ss'))
const siteStatus = ref<any[]>([])
const schedule = ref<ScheduleConfig | null>(null)
const adding = ref(false)
const newTime = ref('')

const taskLoading = ref(false)
const taskData = reactive<{ records: TaskVO[]; total: number; pageNum: number; pageSize: number; pages: number }>({
  records: [], total: 0, pageNum: 1, pageSize: 20, pages: 0
})
const taskFilter = reactive({ status: '', pageNum: 1, pageSize: 20 })

const logFilter = reactive({ level: '' })
const logs = ref<{ time: string; level: string; site: string; message: string }[]>([])

const triggerDialog = reactive({ visible: false, loading: false, form: { siteCode: '', rankingType: 'daily' } })
const logDialog = reactive({ visible: false, taskId: 0, logs: [] as any[] })

let timer: any

const statusType = (s: string) => {
  switch (s) {
    case 'success': case 'INFO': return 'success'
    case 'failed': case 'ERROR': return 'danger'
    case 'running': return 'warning'
    case 'pending': return 'info'
    case 'WARN': return 'warning'
    case 'cancelled': return 'info'
    default: return ''
  }
}
const logLevelClass = (l: string) => 'log-' + l.toLowerCase()

const fetchSiteStatus = async () => { siteStatus.value = await dashboardSites() }
const fetchSchedule = async () => { schedule.value = await getSchedule() }
const fetchTasks = async () => {
  taskLoading.value = true
  try {
    const resp = await listTasks({ ...taskFilter, pageSize: taskFilter.pageSize })
    Object.assign(taskData, resp)
  } finally {
    taskLoading.value = false
  }
}
const fetchLogs = async () => {
  const resp = await listDashboardLogs({ level: logFilter.level || undefined, limit: 100 })
  logs.value = resp.records
}

const addTime = () => {
  if (!newTime.value) { adding.value = false; return }
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(newTime.value)) {
    ElMessage.error('时间格式 HH:mm')
    return
  }
  schedule.value!.dailyCrawlTimes.push(newTime.value)
  schedule.value!.dailyCrawlTimes.sort()
  newTime.value = ''
  adding.value = false
}
const removeTime = (idx: number) => { schedule.value!.dailyCrawlTimes.splice(idx, 1) }

const saveSchedule = async () => {
  await updateSchedule({
    dailyCrawlTimes: schedule.value!.dailyCrawlTimes,
    maxConcurrentTasks: schedule.value!.maxConcurrentTasks,
    taskTimeoutMinutes: schedule.value!.taskTimeoutMinutes
  })
  ElMessage.success('已保存,5 分钟内 Python 生效')
}

const triggerSite = (siteCode: string) => {
  triggerDialog.form.siteCode = siteCode
  triggerDialog.form.rankingType = 'daily'
  triggerDialog.visible = true
}
const confirmTrigger = async () => {
  triggerDialog.loading = true
  try {
    await createTask(triggerDialog.form)
    ElMessage.success('已加入队列')
    triggerDialog.visible = false
    fetchTasks()
  } finally {
    triggerDialog.loading = false
  }
}

const cancelTask = async (id: number) => {
  await ElMessageBox.confirm('确定取消该任务?', '提示', { type: 'warning' })
    .catch(() => null)
    .then(async (ok) => {
      if (ok) {
        await apiCancelTask(id)
        ElMessage.success('已取消')
        fetchTasks()
      }
    })
}

const retryTask = async (id: number) => {
  const r = await apiRetryTask(id)
  ElMessage.success(`新任务 #${r.taskId} 已创建`)
  fetchTasks()
}

const viewLog = async (id: number) => {
  const resp = await getTaskLog(id)
  logDialog.taskId = id
  logDialog.logs = resp.logs
  logDialog.visible = true
}

onMounted(async () => {
  await meta.loadAll()
  await Promise.all([fetchSiteStatus(), fetchSchedule(), fetchTasks(), fetchLogs()])
  timer = setInterval(() => {
    now.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
    fetchLogs()
    if (taskData.records.some(t => t.status === 'pending' || t.status === 'running')) {
      fetchTasks()
    }
  }, 5000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.page { max-width: 1400px; margin: 0 auto; }
.now { color: #909399; }
.block { margin-bottom: 16px; }
.row-between { display: flex; justify-content: space-between; align-items: center; }
.site-card { margin-bottom: 8px; }
.site-head { display: flex; justify-content: space-between; align-items: center; }
.mt { margin-top: 8px; }
.warn { color: #f56c6c; font-size: 12px; }
.time-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
.pager { margin-top: 12px; justify-content: flex-end; display: flex; }
.log-stream { max-height: 360px; overflow-y: auto; background: #1e1e1e; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px; }
.log-line { color: #d4d4d4; line-height: 1.6; }
.log-line .time { color: #858585; margin-right: 8px; }
.log-line .level { margin-right: 8px; }
.log-line .site { color: #4ec9b0; margin-right: 8px; }
.log-info { color: #d4d4d4; }
.log-warn { color: #dcdcaa; }
.log-error { color: #f48771; }
</style>
