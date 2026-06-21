<template>
  <div class="page">
    <!-- ============================================================
         模块 1: 全站数据概览
    ============================================================ -->
    <el-card class="block">
      <h3>数据概览</h3>
      <div class="overview-grid">
        <div v-for="s in overview" :key="s.siteId" class="site-card" :style="{ borderTopColor: s.color }">
          <div class="site-name" :style="{ color: s.color }">{{ s.siteName }}</div>
          <div class="site-stats">
            <div class="stat"><span class="stat-val">{{ s.novelCount }}</span><span class="stat-label">小说</span></div>
            <div class="stat"><span class="stat-val">{{ s.recordCount }}</span><span class="stat-label">记录</span></div>
          </div>
          <div class="site-time" v-if="s.lastCrawl">{{ formatShort(s.lastCrawl) }}</div>
          <div class="site-time muted" v-else>暂无数据</div>
        </div>
      </div>
      <v-chart v-if="overview.length" class="chart" :option="overviewPieOpt" autoresize />
      <el-empty v-if="!overview.length" description="暂无概览数据" :image-size="60" />
    </el-card>

    <div class="two-col">
      <!-- ============================================================
           模块 2: 分类热度排行
      ============================================================ -->
      <el-card class="block">
        <h3>分类热度</h3>
        <v-chart v-if="categories.length" class="chart" :option="categoryBarOpt" autoresize />
        <el-empty v-if="!categories.length" description="暂无分类数据" :image-size="60" />
      </el-card>

      <!-- ============================================================
           模块 3: 跨站 TOP
      ============================================================ -->
      <el-card class="block">
        <div class="section-header">
          <h3>跨站 TOP</h3>
          <div class="section-filters">
            <el-select v-model="topBy" size="small" style="width:100px" @change="fetchTop">
              <el-option label="浏览量" value="viewCount" />
              <el-option label="推荐数" value="recCount" />
              <el-option label="排名" value="rank" />
            </el-select>
            <el-input-number v-model="topLimit" :min="5" :max="50" :step="5" size="small" style="width:90px" @change="fetchTop" />
          </div>
        </div>
        <div class="table-wrap">
          <el-table :data="topListData" size="small" stripe :show-header="topListData.length > 0">
            <el-table-column prop="rank" label="#" width="48" align="center" />
            <el-table-column prop="title" label="书名" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="link-title" @click="addToCompare(row.novelId, row.title)" :title="'添加到趋势对比'">{{ row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="站点" width="90">
              <template #default="{ row }">
                <el-tag :color="row.color" effect="dark" size="small" style="border-color:transparent;color:#fff">{{ row.siteName }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数据" min-width="90" align="right">
              <template #default="{ row }">{{ formatNum(topBy === 'rank' ? row.rank : (topBy === 'recCount' ? row.recCount : row.viewCount)) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- ============================================================
         模块 4: 小说趋势对比
    ============================================================ -->
    <el-card class="block">
      <h3>趋势对比</h3>
      <div class="compare-bar">
        <div class="compare-search">
          <el-select
            v-model="compareNovelIds"
            multiple
            filterable
            remote
            reserve-keyword
            placeholder="搜索书名或作者..."
            :remote-method="onSearchNovels"
            :loading="searchLoading"
            style="flex:1;max-width:500px"
            value-key="novelId"
            @change="onCompareSelectionChange"
            @remove-tag="onRemoveCompareNovel"
          >
            <el-option
              v-for="n in searchResults"
              :key="n.novelId"
              :label="`${n.title} - ${n.author}`"
              :value="n.novelId"
            />
          </el-select>
          <el-select v-model="compareMetric" size="small" style="width:100px">
            <el-option label="浏览量" value="viewCount" />
            <el-option label="推荐数" value="recCount" />
            <el-option label="排名" value="rank" />
          </el-select>
          <el-input-number v-model="compareDays" :min="1" :max="90" :step="1" size="small" style="width:90px" />
          <span class="suffix">天</span>
          <el-button type="primary" size="small" @click="onCompare" :disabled="compareNovelIds.length === 0">对比</el-button>
        </div>
        <div class="compare-tags" v-if="compareTitles.length > 0">
          <el-tag v-for="t in compareTitles" :key="t.novelId" closable type="info" size="small" @close="removeCompareNovel(t.novelId)">
            {{ t.title }}
          </el-tag>
        </div>
      </div>
      <v-chart v-if="series.length > 0" class="chart" :option="compareOpt" autoresize />
      <el-empty v-if="series.length === 0" description="选择小说后点击「对比」查看趋势" :image-size="80" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { compareTrend, topList, fetchTrendOverview, fetchCategoryHeat, searchNovels, type SiteOverviewVO, type CategoryHeatVO, type TrendSeries } from '@/api/rankings'
import dayjs from 'dayjs'

use([CanvasRenderer, LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

/* ============================================================
 * 概览
 * ============================================================ */
const overview = ref<SiteOverviewVO[]>([])
const categories = ref<CategoryHeatVO[]>([])

const formatShort = (t: string | null) => {
  if (!t) return '-'
  const d = dayjs(t)
  return d.isValid() ? d.format('MM-DD HH:mm') : '-'
}

const overviewPieOpt = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 本 ({d}%)' },
  legend: { bottom: 0, type: 'scroll' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '45%'],
    itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
    label: { show: true, formatter: '{b}\n{c} 本' },
    data: overview.value.map(s => ({ name: s.siteName, value: s.novelCount, itemStyle: { color: s.color } }))
  }]
}))

const categoryBarOpt = computed(() => {
  const data = [...categories.value].sort((a, b) => b.novelCount - a.novelCount).slice(0, 15)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 70, right: 20, top: 10, bottom: 20 },
    xAxis: { type: 'value', name: '本数' },
    yAxis: { type: 'category', data: data.map(c => c.category).reverse(), inverse: true },
    series: [{
      type: 'bar',
      data: data.map(c => c.novelCount).reverse(),
      itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  }
})

/* ============================================================
 * 跨站 TOP
 * ============================================================ */
const topListData = ref<any[]>([])
const topBy = ref('viewCount')
const topLimit = ref(20)

const fetchTop = async () => {
  topListData.value = await topList({ limit: topLimit.value, by: topBy.value })
}

/* ============================================================
 * 小说搜索 & 对比
 * ============================================================ */
const searchResults = ref<{ novelId: number; title: string; author: string; siteId: number }[]>([])
const searchLoading = ref(false)
const compareNovelIds = ref<number[]>([])
const compareTitles = ref<{ novelId: number; title: string }[]>([])
const compareMetric = ref<'viewCount' | 'recCount' | 'rank'>('viewCount')
const compareDays = ref(7)
const series = ref<TrendSeries[]>([])

const compareOpt = computed(() => {
  const allTimes = new Set<string>()
  series.value.forEach(s => s.points.forEach((p: any) => allTimes.add(p.time)))
  const times = Array.from(allTimes).sort()
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: series.value.map(s => s.title), bottom: 0, type: 'scroll' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: times },
    yAxis: compareMetric.value === 'rank' ? { type: 'value', inverse: true, name: '排名' } : { type: 'value', name: compareMetric.value === 'recCount' ? '推荐数' : '浏览量' },
    series: series.value.map(s => ({
      name: s.title,
      type: 'line',
      smooth: true,
      data: times.map(t => s.points.find((p: any) => p.time === t)?.value ?? null),
      lineStyle: { color: s.color || '#409eff' }
    }))
  }
})

const onSearchNovels = async (kw: string) => {
  if (!kw || kw.length < 1) { searchResults.value = []; return }
  searchLoading.value = true
  try {
    searchResults.value = await searchNovels(kw, 20)
  } finally {
    searchLoading.value = false
  }
}

const onCompareSelectionChange = (ids: number[]) => {
  // 保留已选标题
  const newTitles = [...compareTitles.value]
  // 新增的ID
  for (const id of ids) {
    if (!newTitles.find(t => t.novelId === id)) {
      const found = searchResults.value.find(n => n.novelId === id)
      if (found) newTitles.push({ novelId: found.novelId, title: found.title })
    }
  }
  // 移除取消的ID
  const keepIds = new Set(ids)
  compareTitles.value = newTitles.filter(t => keepIds.has(t.novelId)).slice(0, 5)
  compareNovelIds.value = compareTitles.value.map(t => t.novelId)
}

const addToCompare = (novelId: number, title: string) => {
  if (compareTitles.value.length >= 5) return
  if (!compareTitles.value.find(t => t.novelId === novelId)) {
    compareTitles.value.push({ novelId, title })
    compareNovelIds.value = compareTitles.value.map(t => t.novelId)
  }
}

const removeCompareNovel = (novelId: number) => {
  compareTitles.value = compareTitles.value.filter(t => t.novelId !== novelId)
  compareNovelIds.value = compareTitles.value.map(t => t.novelId)
}

const onRemoveCompareNovel = (id: number) => removeCompareNovel(id)

const onCompare = async () => {
  if (compareNovelIds.value.length === 0) return
  const resp = await compareTrend({ novelIds: compareNovelIds.value, metric: compareMetric.value, days: compareDays.value })
  series.value = resp.series
}

// 自动对比当选中变化时
watch([compareMetric, compareDays], () => {
  if (compareNovelIds.value.length > 0) onCompare()
})

/* ============================================================
 * 工具
 * ============================================================ */
const formatNum = (n: number) => {
  if (n === undefined || n === null) return '-'
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

onMounted(async () => {
  const [ov, cat] = await Promise.all([fetchTrendOverview(), fetchCategoryHeat()])
  overview.value = ov
  categories.value = cat
  fetchTop()
})
</script>

<style scoped>
.page {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.block {
  margin-bottom: 16px;
}

.block h3 {
  margin: 0 0 12px;
}

/* 概览网格 */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.site-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-top: 3px solid #409eff;
  border-radius: 8px;
  padding: 12px 16px;
  transition: box-shadow 0.2s;
}

.site-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.site-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}

.site-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 6px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-val {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

.site-time {
  font-size: 11px;
  color: #606266;
}

.site-time.muted {
  color: #c0c4cc;
}

/* 双列 */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* 图表 */
.chart {
  height: 320px;
  width: 100%;
}

/* TOP 头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-header h3 {
  margin: 0;
}

.section-filters {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 对比条 */
.compare-bar {
  margin-bottom: 12px;
}

.compare-search {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.compare-tags {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.suffix {
  color: #909399;
  font-size: 13px;
}

.link-title {
  color: #409eff;
  cursor: pointer;
}

.link-title:hover {
  text-decoration: underline;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .two-col {
    grid-template-columns: 1fr;
  }
  .chart {
    height: 260px;
  }
  .overview-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
</style>
