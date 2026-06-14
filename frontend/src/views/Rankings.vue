<template>
  <div class="page">
    <el-card>
      <div class="header-row">
        <h2>排行榜</h2>
        <span class="meta" v-if="data.total > 0">共 {{ data.total }} 条,最新抓取于 {{ lastTime }}</span>
      </div>

      <el-form :inline="true" class="filter-bar">
        <el-form-item label="站点">
          <el-select v-model="filters.site" placeholder="选择站点" filterable @change="onChange">
            <el-option v-for="s in sites" :key="s.code" :label="s.name" :value="s.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="榜单类型">
          <el-select v-model="filters.type" filterable @change="onChange">
            <el-option v-for="t in meta.rankingTypes" :key="t.code" :label="t.name" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="小说类型">
          <el-select v-model="filters.category" placeholder="全部类型" clearable filterable @change="onChange">
            <el-option v-for="c in meta.categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="filters.keyword" placeholder="书名/作者" clearable @keyup.enter="onChange" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onChange">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="data.records" v-loading="loading" stripe @row-click="goDetail" style="cursor: pointer">
        <el-table-column label="排名" prop="rank" width="70" align="center" />
        <el-table-column label="书名" prop="title" min-width="200" />
        <el-table-column label="作者" prop="author" width="120" />
        <el-table-column label="分类" prop="category" width="100" />
        <el-table-column label="浏览量" width="120" align="right">
          <template #default="{ row }">{{ formatNum(row.viewCount) }}</template>
        </el-table-column>
        <el-table-column label="推荐数" width="100" align="right">
          <template #default="{ row }">{{ formatNum(row.recCount) }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无数据,请选择站点和榜单类型后查询" :image-size="80" />
        </template>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, prev, pager, next, jumper"
        :total="data.total"
        :current-page="filters.pageNum"
        :page-size="filters.pageSize"
        @current-change="onPageChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listRankings, type RankingItemVO } from '@/api/rankings'
import { listEnabledSites, type SiteVO } from '@/api/sites'
import { useMetaStore } from '@/stores/meta'
import dayjs from 'dayjs'

const router = useRouter()
const meta = useMetaStore()
const sites = ref<SiteVO[]>([])
const loading = ref(false)
const data = reactive<{ records: RankingItemVO[]; total: number; pageNum: number; pageSize: number; pages: number }>({
  records: [], total: 0, pageNum: 1, pageSize: 20, pages: 0
})
const filters = reactive({
  site: '' as string,
  type: 'daily' as string,
  category: '' as string,
  keyword: '' as string,
  pageNum: 1,
  pageSize: 20
})
const lastTime = ref('')

const formatNum = (n: number) => {
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

const fetchSites = async () => {
  sites.value = await listEnabledSites()
  if (sites.value.length && !filters.site) {
    filters.site = sites.value[0].code
  }
}

const fetchData = async () => {
  if (!filters.site || !filters.type) return
  // 分类榜需要先选分类,否则后端会拒绝
  if (filters.type === 'category' && !filters.category) {
    data.records = []
    data.total = 0
    loading.value = false
    return
  }
  loading.value = true
  try {
    const resp = await listRankings({
      site: filters.site,
      type: filters.type,
      category: filters.category || undefined,
      keyword: filters.keyword || undefined,
      pageNum: filters.pageNum,
      pageSize: filters.pageSize
    })
    Object.assign(data, resp)
    if (resp.records.length) {
      lastTime.value = dayjs(resp.records[0].crawlTime || new Date()).format('YYYY-MM-DD HH:mm')
    }
  } catch {
    // 错误已由拦截器提示
    data.records = []
    data.total = 0
  } finally {
    loading.value = false
  }
}

const onChange = () => {
  // 切换到分类榜时,自动选中第一个分类,避免后端校验失败
  if (filters.type === 'category' && !filters.category && meta.categories.length > 0) {
    filters.category = meta.categories[0]
  }
  filters.pageNum = 1
  fetchData()
}
const onPageChange = (p: number) => { filters.pageNum = p; fetchData() }
const goDetail = (row: RankingItemVO) => {
  if (!row.novelId) return
  router.push(`/novels/${row.novelId}`)
}

onMounted(async () => {
  await meta.loadAll()
  await fetchSites()
  // fetchSites sets filters.site, then fetch data
  if (filters.site) await fetchData()
})
</script>

<style scoped>
.page { max-width: 1200px; margin: 0 auto; }
.header-row { display: flex; align-items: baseline; gap: 16px; margin-bottom: 16px; }
.header-row h2 { margin: 0; }
.meta { color: #909399; font-size: 13px; }
.filter-bar { margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; display: flex; }
</style>
