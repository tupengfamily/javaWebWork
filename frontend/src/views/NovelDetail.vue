<template>
  <div class="page" v-loading="loading">
    <el-button @click="$router.back()" class="back">← 返回</el-button>

    <el-card v-if="novel" class="info-card">
      <div class="info-row">
        <el-image v-if="novel.coverUrl" :src="novel.coverUrl" class="cover" fit="cover" />
        <div class="meta">
          <h2>{{ novel.title }}</h2>
          <p>作者: {{ novel.author }} | 分类: {{ novel.category }} | 字数: {{ novel.wordCount }}</p>
          <p>状态: {{ novel.status }} | 来源: {{ novel.siteName }}</p>
          <p>最近抓取: {{ novel.lastCrawlTime }}</p>
          <el-link :href="novel.novelUrl" target="_blank" type="primary">跳转原文 ↗</el-link>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="charts">
      <el-col :span="12">
        <el-card>
          <h3>排名趋势</h3>
          <el-empty v-if="trend.ranking.length === 0" description="暂无排名数据" :image-size="60" />
          <v-chart v-else class="chart" :option="rankChartOpt" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <h3>浏览量趋势</h3>
          <el-empty v-if="trend.viewCount.length === 0" description="暂无浏览量数据" :image-size="60" />
          <v-chart v-else class="chart" :option="viewChartOpt" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <h3>历史快照</h3>
      <el-table :data="records" stripe>
        <el-table-column prop="crawlTime" label="时间" width="180" />
        <el-table-column prop="rankingType" label="榜单" width="100" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="rank" label="排名" width="80" align="center" />
        <el-table-column prop="viewCount" label="浏览量" align="right">
          <template #default="{ row }">{{ formatNum(row.viewCount) }}</template>
        </el-table-column>
        <el-table-column prop="recCount" label="推荐数" align="right">
          <template #default="{ row }">{{ formatNum(row.recCount) }}</template>
        </el-table-column>
      </el-table>
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
    // trend 数据可选,加载失败不阻断页面
  }
  loading.value = false
}

const fetchRecords = async () => {
  try {
    const resp = await getNovelRecords(id, { pageNum: recordsPage.value, pageSize: 20 })
    records.value = resp.records || []
    recordsTotal.value = resp.total || 0
  } catch {
    // 历史快照加载失败不影响详情展示
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
.page { max-width: 1200px; margin: 0 auto; }
.back { margin-bottom: 12px; }
.info-card { margin-bottom: 16px; }
.info-row { display: flex; gap: 24px; }
.cover { width: 120px; height: 160px; border-radius: 4px; }
.meta h2 { margin: 0 0 12px; }
.meta p { margin: 4px 0; color: #606266; }
.charts { margin-bottom: 16px; }
.chart { height: 300px; }
.table-card { margin-bottom: 24px; }
.pager { margin-top: 12px; justify-content: flex-end; display: flex; }
</style>
