<template>
  <div class="page">
    <el-card>
      <h2>趋势分析</h2>
      <el-form :inline="true" class="filter-bar">
        <el-form-item label="指标">
          <el-select v-model="metric" style="width: 140px">
            <el-option label="排名" value="rank" />
            <el-option label="浏览量" value="viewCount" />
            <el-option label="推荐数" value="recCount" />
          </el-select>
        </el-form-item>
        <el-form-item label="近">
          <el-input-number v-model="days" :min="1" :max="90" :step="1" />
          <span class="suffix">天</span>
        </el-form-item>
        <el-form-item label="小说ID(逗号分隔,最多5个)">
          <el-input v-model="novelIdsInput" placeholder="如 1,2,3" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onCompare">对比</el-button>
          <el-button @click="fetchTop">刷新 TOP</el-button>
        </el-form-item>
      </el-form>

      <h3>对比图</h3>
      <v-chart class="chart" :option="compareOpt" autoresize />

      <h3>跨站 TOP 10</h3>
      <el-table :data="topListData" stripe>
        <el-table-column prop="rank" label="排名" width="70" align="center" />
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column label="站点" width="100">
          <template #default="{ row }">
            <el-tag :color="row.color" effect="dark" style="border-color: transparent; color: #fff">{{ row.siteName }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="浏览量" align="right">
          <template #default="{ row }">{{ formatNum(row.viewCount) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { compareTrend, topList } from '@/api/rankings'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const metric = ref<'rank' | 'viewCount' | 'recCount'>('viewCount')
const days = ref(7)
const novelIdsInput = ref('1')
const series = ref<any[]>([])
const topListData = ref<any[]>([])

const formatNum = (n: number) => {
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

const compareOpt = computed(() => {
  const allTimes = new Set<string>()
  series.value.forEach(s => s.points.forEach((p: any) => allTimes.add(p.time)))
  const times = Array.from(allTimes).sort()
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: series.value.map(s => s.title) },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: times },
    yAxis: metric.value === 'rank' ? { type: 'value', inverse: true } : { type: 'value' },
    series: series.value.map(s => ({
      name: s.title,
      type: 'line',
      smooth: true,
      data: times.map(t => s.points.find((p: any) => p.time === t)?.value ?? null)
    }))
  }
})

const onCompare = async () => {
  const ids = novelIdsInput.value.split(',').map(s => Number(s.trim())).filter(n => !isNaN(n)).slice(0, 5)
  if (ids.length === 0) return
  const resp = await compareTrend({ novelIds: ids, metric: metric.value, days: days.value })
  series.value = resp.series
}

const fetchTop = async () => {
  topListData.value = await topList({ limit: 10, by: 'viewCount' })
}

onMounted(() => {
  fetchTop()
})
</script>

<style scoped>
.page { max-width: 1200px; margin: 0 auto; }
.filter-bar { margin: 16px 0; }
.suffix { margin-left: 8px; }
.chart { height: 380px; }
</style>
