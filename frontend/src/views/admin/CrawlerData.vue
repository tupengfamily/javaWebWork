<template>
  <div class="page">
    <h2>爬取数据管理</h2>

    <!-- 小说列表 -->
    <el-card class="block">
      <div class="row-between">
        <h3>小说列表</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          <el-select v-model="novelFilter.siteId" placeholder="站点" clearable @change="fetchNovels" style="width:130px">
            <el-option v-for="s in siteStatus" :key="s.siteId" :label="s.siteName" :value="s.siteId" />
          </el-select>
          <el-input v-model="novelFilter.keyword" placeholder="书名/作者" clearable style="width:160px" @keyup.enter="fetchNovels" @clear="fetchNovels" />
          <el-button @click="fetchNovels">搜索</el-button>
          <el-popconfirm title="确定删除所选小说?（关联排行数据也会删除）" @confirm="batchDeleteNovels">
            <template #reference>
              <el-button :disabled="novelSelection.length === 0" type="danger">批量删除</el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
      <div class="table-wrap">
        <el-table :data="novelData.records" v-loading="novelLoading" stripe @selection-change="(rows: any[]) => novelSelection = rows.map(r => r.id)">
          <el-table-column type="selection" width="40" />
          <el-table-column prop="id" label="ID" width="65" />
          <el-table-column prop="title" label="书名" min-width="150" show-overflow-tooltip />
          <el-table-column prop="author" label="作者" min-width="90" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" min-width="70" />
          <el-table-column label="字数" min-width="80" align="right">
            <template #default="{ row }">{{ formatNum(row.wordCount) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" min-width="70" />
          <el-table-column label="最近爬取" min-width="150">
            <template #default="{ row }">{{ formatTime(row.lastCrawlTime) }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="120" fixed="right">
            <template #default="{ row }">
              <el-popconfirm title="确定删除该小说及关联排行数据?" @confirm="deleteNovel(row.id)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
              <el-button size="small" type="primary" link @click="viewNovelRecords(row.id)">排行记录</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        background layout="total, prev, pager, next, jumper"
        :total="novelData.total" :current-page="novelFilter.pageNum"
        @current-change="(p: number) => { novelFilter.pageNum = p; fetchNovels() }"
        class="pager"
      />
    </el-card>

    <!-- 排行记录弹窗 -->
    <el-dialog v-model="recordDialog.visible" :title="`小说 #${recordDialog.novelId} 排行记录`" width="800px">
      <el-table :data="recordDialog.records" v-loading="recordDialog.loading" max-height="400" stripe>
        <el-table-column prop="id" label="ID" width="65" />
        <el-table-column prop="rankingType" label="榜单" min-width="80" />
        <el-table-column prop="rank" label="排名" width="65" align="center" />
        <el-table-column prop="viewCount" label="浏览量" min-width="90" align="right">
          <template #default="{ row }">{{ formatNum(row.viewCount) }}</template>
        </el-table-column>
        <el-table-column label="爬取时间" min-width="160">
          <template #default="{ row }">{{ formatTime(row.crawlTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row: r }">
            <el-popconfirm title="删除该记录?" @confirm="deleteRecord(r.id)">
              <template #reference>
                <el-button size="small" type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { dashboardSites } from '@/api/tasks'
import request from '@/utils/request'

const siteStatus = ref<any[]>([])

const novelLoading = ref(false)
const novelData = reactive({ records: [] as any[], total: 0, pageNum: 1, pageSize: 20, pages: 0 })
const novelFilter = reactive({ keyword: '', siteId: null as number | null, pageNum: 1, pageSize: 20 })
const novelSelection = ref<number[]>([])

const recordDialog = reactive({ visible: false, loading: false, novelId: 0, records: [] as any[] })

const formatTime = (t: string | null) => {
  if (!t) return '-'
  if (typeof t !== 'string') return String(t)
  const d = dayjs(t)
  return d.isValid() ? d.format('MM-DD HH:mm:ss') : t
}

const formatNum = (n: number) => {
  if (!n && n !== 0) return '-'
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

const fetchSiteStatus = async () => { siteStatus.value = await dashboardSites() }

const fetchNovels = async () => {
  novelLoading.value = true
  try {
    const params: any = { pageNum: novelFilter.pageNum, pageSize: novelFilter.pageSize }
    if (novelFilter.keyword) params.keyword = novelFilter.keyword
    if (novelFilter.siteId) params.siteId = novelFilter.siteId
    const resp = await request.get<any, any>('/admin/novels', { params })
    Object.assign(novelData, resp)
  } finally {
    novelLoading.value = false
  }
}

const deleteNovel = async (id: number) => {
  await request.delete(`/admin/novels/${id}`)
  ElMessage.success('已删除')
  fetchNovels()
}

const batchDeleteNovels = async () => {
  if (novelSelection.value.length === 0) return
  await request.delete('/admin/novels/batch', { data: novelSelection.value })
  ElMessage.success(`已删除 ${novelSelection.value.length} 本小说`)
  novelSelection.value = []
  fetchNovels()
}

const viewNovelRecords = async (novelId: number) => {
  recordDialog.novelId = novelId
  recordDialog.records = []
  recordDialog.visible = true
  recordDialog.loading = true
  try {
    const resp = await request.get<any, any>('/admin/novels/records', { params: { pageNum: 1, pageSize: 100, novelId } })
    recordDialog.records = resp.records || []
  } finally {
    recordDialog.loading = false
  }
}

const deleteRecord = async (recordId: number) => {
  await request.delete(`/admin/novels/records/${recordId}`)
  ElMessage.success('记录已删除')
  recordDialog.records = recordDialog.records.filter((r: any) => r.id !== recordId)
}

onMounted(async () => {
  await Promise.all([fetchSiteStatus(), fetchNovels()])
})
</script>

<style scoped>
.page {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.block { margin-bottom: 16px; }

.row-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.row-between h3 { margin: 0; }

.table-wrap { width: 100%; overflow-x: auto; }

.pager { margin-top: 12px; justify-content: flex-end; display: flex; }

@media (max-width: 576px) {
  .row-between h3 { font-size: 15px; }
}
</style>
