<template>
  <div class="page" v-loading="loading">
    <el-button @click="$router.back()" class="back">← 返回</el-button>

    <el-card v-if="novel" class="info-card">
      <div class="info-row">
        <el-image v-if="novel.coverUrl" :src="novel.coverUrl" class="cover" fit="cover" />
        <div class="meta">
          <h2>{{ novel.title }}</h2>
          <p>作者: {{ novel.author }} | 分类: {{ novel.category }} | 字数: {{ formatNum(novel.wordCount) }}</p>
          <p>状态: {{ novel.status }} | 来源: {{ novel.siteName }}</p>
          <p>最近抓取: {{ novel.lastCrawlTime }}</p>
          <el-link :href="novel.novelUrl" target="_blank" type="primary">跳转原文 ↗</el-link>
        </div>
      </div>
    </el-card>

    <!-- 故事大纲 & 角色说明 -->
    <el-row :gutter="16" class="content-section">
      <el-col :xs="24" :md="12">
        <el-card class="content-card">
          <h3>故事大纲</h3>
          <div v-if="novel.outline" class="text-content">{{ novel.outline }}</div>
          <el-empty v-else description="暂无故事大纲" :image-size="50" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card class="content-card">
          <h3>角色说明</h3>
          <div v-if="novel.characters" class="text-content">{{ novel.characters }}</div>
          <el-empty v-else description="暂无角色说明" :image-size="50" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts">
      <el-col :xs="24" :sm="12">
        <el-card class="chart-card">
          <h3>排名趋势</h3>
          <el-empty v-if="trend.ranking.length === 0" description="暂无排名数据" :image-size="60" />
          <v-chart v-else class="chart" :option="rankChartOpt" autoresize />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="chart-card">
          <h3>浏览量趋势</h3>
          <el-empty v-if="trend.viewCount.length === 0" description="暂无浏览量数据" :image-size="60" />
          <v-chart v-else class="chart" :option="viewChartOpt" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <h3>历史快照</h3>
      <div class="table-wrap">
        <el-table :data="records" stripe>
          <el-table-column prop="crawlTime" label="时间" min-width="160" />
          <el-table-column prop="rankingType" label="榜单" min-width="90" />
          <el-table-column prop="category" label="分类" min-width="90" />
          <el-table-column prop="rank" label="排名" width="70" align="center" />
          <el-table-column prop="viewCount" label="浏览量" min-width="100" align="right">
            <template #default="{ row }">{{ formatNum(row.viewCount) }}</template>
          </el-table-column>
          <el-table-column prop="recCount" label="推荐数" min-width="90" align="right">
            <template #default="{ row }">{{ formatNum(row.recCount) }}</template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        background layout="total, prev, pager, next, jumper"
        :total="recordsTotal" :current-page="recordsPage"
        @current-change="(p) => { recordsPage = p; fetchRecords() }"
        class="pager"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getNovel, getNovelTrend, getNovelRecords, type NovelVO } from '@/api/novels'
import dayjs from 'dayjs'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const route = useRoute()
const id = Number(route.params.id)

const loading = ref(false)
const novel = ref<NovelVO | null>(null)
const trend = ref<{ ranking: any[]; viewCount: any[]; recCount: any[] }>({ ranking: [], viewCount: [], recCount: [] })
const records = ref<any[]>([])
const recordsTotal = ref(0)
const recordsPage = ref(1)

const formatNum = (n: number) => {
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

const baseLineOpt = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: [] as string[] },
  yAxis: { type: 'value' }
}))

const rankChartOpt = computed(() => ({
  ...baseLineOpt.value,
  yAxis: { type: 'value', inverse: true },
  xAxis: { type: 'category', data: trend.value.ranking.map(p => p.time) },
  series: [{ name: '排名', type: 'line', data: trend.value.ranking.map(p => p.value), smooth: true }]
}))

const viewChartOpt = computed(() => ({
  ...baseLineOpt.value,
  xAxis: { type: 'category', data: trend.value.viewCount.map(p => p.time) },
  series: [{ name: '浏览量', type: 'line', data: trend.value.viewCount.map(p => p.value), smooth: true, areaStyle: {} }]
}))

const fetchNovel = async () => {
  loading.value = true
  try {
    novel.value = await getNovel(id)
  } catch {
    ElMessage.error('小说不存在或已被删除')
    loading.value = false
    return
  }
  try {
    const t = await getNovelTrend(id, { type: 'daily', days: 30 })
    trend.value = t
  } catch {
    // trend 数据可选
  }
  loading.value = false
}

const fetchRecords = async () => {
  try {
    const resp = await getNovelRecords(id, { pageNum: recordsPage.value, pageSize: 20 })
    records.value = resp.records || []
    recordsTotal.value = resp.total || 0
  } catch {
    records.value = []
    recordsTotal.value = 0
  }
}

onMounted(async () => {
  await fetchNovel()
  await fetchRecords()
})
</script>

<style scoped>
.page {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.back { margin-bottom: 12px; }

.info-card { margin-bottom: 16px; }

.info-row {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.cover {
  width: 120px;
  height: 160px;
  border-radius: 4px;
  flex-shrink: 0;
}

.meta { flex: 1; min-width: 0; }
.meta h2 { margin: 0 0 12px; }
.meta p { margin: 4px 0; color: #606266; }

.content-section { margin-bottom: 16px; }

.content-card {
  margin-bottom: 12px;
  min-height: 160px;
}

.text-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
}

.charts { margin-bottom: 16px; }

.chart-card { margin-bottom: 12px; }

.chart { height: 300px; width: 100%; }

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.table-card { margin-bottom: 24px; }

.pager {
  margin-top: 12px;
  justify-content: flex-end;
  display: flex;
}

@media (max-width: 768px) {
  .info-row {
    flex-direction: column;
    gap: 12px;
  }
  .cover {
    width: 80px;
    height: 106px;
  }
  .chart { height: 240px; }
}

@media (max-width: 576px) {
  .chart { height: 200px; }
}
</style>
