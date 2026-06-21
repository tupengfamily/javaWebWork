<template>
  <div class="page">
    <el-card>
      <div class="header-row">
        <h2>排行榜</h2>
        <span class="meta" v-if="data.total > 0">共 {{ data.total }} 条，最新抓取于 {{ lastTime }}</span>
        <div class="header-actions">
          <!-- 文字显示切换 -->
          <el-tooltip :content="textWrap ? '切换为单行截断' : '切换为多行显示'">
            <el-button :icon="textWrap ? 'Memo' : 'Document'" circle size="small"
              @click="textWrap = !textWrap; saveTablePrefs()" />
          </el-tooltip>
          <!-- 列设置 -->
          <el-popover placement="bottom-end" :width="240" trigger="click">
            <template #reference>
              <el-button icon="Setting" circle size="small" title="表格列设置" />
            </template>
            <div class="col-setting">
              <div class="col-setting-title">显示字段</div>
              <el-checkbox v-for="col in allColumns" :key="col.key"
                :model-value="visibleKeys.includes(col.key)"
                @change="(v: boolean) => toggleColumn(col.key, v)"
                :disabled="col.key === 'rank'">
                {{ col.label }}
              </el-checkbox>
              <el-divider style="margin: 8px 0" />
              <el-button size="small" text type="primary" @click="resetColumns">恢复默认</el-button>
            </div>
          </el-popover>
        </div>
      </div>

      <el-form :inline="true" class="filter-bar">
        <el-form-item label="站点">
          <el-select v-model="filters.site" filterable @change="onChange">
            <el-option v-for="s in sites" :key="s.code" :label="s.name" :value="s.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="榜单">
          <el-select v-model="filters.type" filterable @change="onChange">
            <el-option v-for="t in meta.rankingTypes" :key="t.code" :label="t.name" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部" clearable filterable @change="onChange">
            <el-option v-for="c in meta.categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="书名/作者" clearable @keyup.enter="onChange" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onChange">查询</el-button>
        </el-form-item>
      </el-form>

      <div class="table-wrap">
        <el-table ref="tableRef" :data="data.records" v-loading="loading" stripe
          :show-overflow-tooltip="!textWrap" @header-dragend="onColResize" style="cursor: default">
          <!-- # rank -->
          <el-table-column v-if="isColVisible('rank')" label="#" prop="rank"
            :width="colWidths.rank || 60" align="center" />

          <!-- 封面 -->
          <el-table-column v-if="isColVisible('coverUrl')" label="封面" prop="coverUrl"
            :width="colWidths.coverUrl || 70" align="center">
            <template #default="{ row }">
              <el-image v-if="row.coverUrl" :src="row.coverUrl" style="width: 40px; height: 54px"
                fit="cover" :preview-src-list="[row.coverUrl]" preview-teleported lazy>
                <template #error>
                  <div class="cover-placeholder">-</div>
                </template>
              </el-image>
              <span v-else class="cover-placeholder">-</span>
            </template>
          </el-table-column>

          <!-- 书名（可点击跳转） -->
          <el-table-column v-if="isColVisible('title')" label="书名" prop="title"
            :min-width="colWidths.title || 200">
            <template #default="{ row }">
              <span v-if="row.novelUrl" class="link-title" @click.stop="openUrl(row)"
                :title="'打开: ' + row.novelUrl">
                {{ row.title }}
              </span>
              <span v-else class="title-text" :title="row.title">{{ row.title }}</span>
            </template>
          </el-table-column>

          <!-- 作者 -->
          <el-table-column v-if="isColVisible('author')" label="作者" prop="author"
            :width="colWidths.author || 110" show-overflow-tooltip />

          <!-- 分类 -->
          <el-table-column v-if="isColVisible('category')" label="分类" prop="category"
            :width="colWidths.category || 80" />

          <!-- 浏览量 -->
          <el-table-column v-if="isColVisible('viewCount')" label="浏览量" prop="viewCount"
            :width="colWidths.viewCount || 100" align="right">
            <template #default="{ row }">{{ formatNum(row.viewCount) }}</template>
          </el-table-column>

          <!-- 推荐数 -->
          <el-table-column v-if="isColVisible('recCount')" label="推荐数" prop="recCount"
            :width="colWidths.recCount || 90" align="right">
            <template #default="{ row }">{{ formatNum(row.recCount) }}</template>
          </el-table-column>

          <!-- 字数 -->
          <el-table-column v-if="isColVisible('wordCount')" label="字数" prop="wordCount"
            :width="colWidths.wordCount || 90" align="right">
            <template #default="{ row }">{{ row.wordCount ? formatNum(row.wordCount) : '-' }}</template>
          </el-table-column>

          <!-- 状态 -->
          <el-table-column v-if="isColVisible('status')" label="状态" prop="status"
            :width="colWidths.status || 80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'completed'" type="success" size="small">完结</el-tag>
              <el-tag v-else-if="row.status === 'ongoing'" type="warning" size="small">连载</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <!-- 简介 -->
          <el-table-column v-if="isColVisible('description')" label="简介" prop="description"
            :min-width="colWidths.description || 240" :show-overflow-tooltip="!textWrap">
            <template #default="{ row }">
              <span class="desc-text">{{ row.description || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 链接 -->
          <el-table-column v-if="isColVisible('novelUrl')" label="链接" prop="novelUrl"
            :width="colWidths.novelUrl || 70" align="center">
            <template #default="{ row }">
              <el-tooltip v-if="row.novelUrl" content="打开原站链接" placement="top">
                <el-icon class="link-icon" @click.stop="openUrl(row)">
                  <Link />
                </el-icon>
              </el-tooltip>
              <el-tooltip v-else content="暂无详情链接" placement="top">
                <el-icon class="link-icon-disabled"><Link /></el-icon>
              </el-tooltip>
            </template>
          </el-table-column>

          <!-- 抓取时间 -->
          <el-table-column v-if="isColVisible('crawlTime')" label="抓取时间" prop="crawlTime"
            :width="colWidths.crawlTime || 140">
            <template #default="{ row }">{{ formatTime(row.crawlTime) }}</template>
          </el-table-column>

          <template #empty>
            <el-empty description="暂无数据，请选择站点和榜单类型后查询" :image-size="80" />
          </template>
        </el-table>
      </div>

      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="data.total"
        :current-page="filters.pageNum"
        :page-size="filters.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listRankings, type RankingItemVO } from '@/api/rankings'
import { listEnabledSites, type SiteVO } from '@/api/sites'
import { useMetaStore } from '@/stores/meta'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

const router = useRouter()
const auth = useAuthStore()
const meta = useMetaStore()
const tableRef = ref()
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

/* ============================================================
 * 列定义 — 所有可能的列
 * ============================================================ */
interface ColDef { key: string; label: string; defaultVisible: boolean }

const allColumns: ColDef[] = [
  { key: 'rank',        label: '排名',     defaultVisible: true },
  { key: 'coverUrl',    label: '封面',     defaultVisible: false },
  { key: 'title',       label: '书名',     defaultVisible: true },
  { key: 'author',      label: '作者',     defaultVisible: true },
  { key: 'category',    label: '分类',     defaultVisible: true },
  { key: 'viewCount',   label: '浏览量',   defaultVisible: true },
  { key: 'recCount',    label: '推荐数',   defaultVisible: true },
  { key: 'wordCount',   label: '字数',     defaultVisible: false },
  { key: 'status',      label: '状态',     defaultVisible: false },
  { key: 'description', label: '简介',     defaultVisible: false },
  { key: 'novelUrl',    label: '链接',     defaultVisible: true },
  { key: 'crawlTime',   label: '抓取时间', defaultVisible: false },
]
const defaultVisibleKeys = allColumns.filter(c => c.defaultVisible).map(c => c.key)

/* ============================================================
 * 表格偏好 — localStorage 持久化
 * - visibleKeys: 可见列
 * - colWidths:   列宽(拖动后记忆)
 * - textWrap:    多行/单行
 * ============================================================ */
const PREFS_KEY = 'rankings:tablePrefs'
const visibleKeys = ref<string[]>([...defaultVisibleKeys])
const colWidths = ref<Record<string, number>>({})
const textWrap = ref(false)

const isColVisible = (key: string) => visibleKeys.value.includes(key)

const loadTablePrefs = () => {
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    if (Array.isArray(saved.visibleKeys) && saved.visibleKeys.length > 0) {
      // 保证 rank 始终存在
      if (!saved.visibleKeys.includes('rank')) saved.visibleKeys.unshift('rank')
      visibleKeys.value = saved.visibleKeys
    }
    if (saved.colWidths && typeof saved.colWidths === 'object') {
      colWidths.value = saved.colWidths
    }
    if (typeof saved.textWrap === 'boolean') {
      textWrap.value = saved.textWrap
    }
  } catch { /* ignore */ }
}

const saveTablePrefs = () => {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({
      visibleKeys: visibleKeys.value,
      colWidths: colWidths.value,
      textWrap: textWrap.value,
    }))
  } catch { /* ignore */ }
}

const toggleColumn = (key: string, show: boolean) => {
  if (key === 'rank') return // rank 不可隐藏
  if (show && !visibleKeys.value.includes(key)) {
    visibleKeys.value.push(key)
  } else if (!show) {
    visibleKeys.value = visibleKeys.value.filter(k => k !== key)
  }
  saveTablePrefs()
}

const resetColumns = () => {
  visibleKeys.value = [...defaultVisibleKeys]
  colWidths.value = {}
  textWrap.value = false
  saveTablePrefs()
  ElMessage.success('已恢复默认列设置')
}

const onColResize = (_newWidth: number, _oldWidth: number, column: any) => {
  const key = column?.property || column?.columnKey
  if (key) {
    colWidths.value[key] = _newWidth
    saveTablePrefs()
  }
}

/* ============================================================
 * 记住查询条件
 * ============================================================ */
const FILTERS_KEY = 'rankings:filters'
const loadSavedFilters = () => {
  try {
    const raw = localStorage.getItem(FILTERS_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    if (saved && typeof saved === 'object') {
      if (typeof saved.site === 'string') filters.site = saved.site
      if (typeof saved.type === 'string') filters.type = saved.type
      if (typeof saved.category === 'string') filters.category = saved.category
      if (typeof saved.keyword === 'string') filters.keyword = saved.keyword
      if (typeof saved.pageNum === 'number') filters.pageNum = saved.pageNum
      if (typeof saved.pageSize === 'number') filters.pageSize = saved.pageSize
    }
  } catch { /* ignore */ }
}
let saveTimer: ReturnType<typeof setTimeout> | null = null
const saveFilters = () => {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    try {
      localStorage.setItem(FILTERS_KEY, JSON.stringify(filters))
    } catch { /* ignore */ }
  }, 300)
}
watch(filters, saveFilters, { deep: true })

/* ============================================================
 * 格式化 & 跳转
 * ============================================================ */
const formatNum = (n: number) => {
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

const formatTime = (t?: string) => {
  if (!t) return '-'
  return dayjs(t).format('MM-DD HH:mm')
}

const openUrl = (row: RankingItemVO) => {
  if (row.novelUrl) {
    window.open(row.novelUrl, '_blank', 'noopener,noreferrer')
  } else {
    ElMessage.info('暂无详情链接，该站点未提供原站地址')
  }
}

/* ============================================================
 * 数据请求
 * ============================================================ */
const fetchSites = async () => {
  sites.value = await listEnabledSites()
  if (sites.value.length && !filters.site) {
    filters.site = sites.value[0].code
  }
}

const fetchData = async () => {
  if (!filters.site || !filters.type) return
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
    data.records = []
    data.total = 0
  } finally {
    loading.value = false
  }
}

const onChange = () => {
  if (filters.type === 'category' && !filters.category && meta.categories.length > 0) {
    filters.category = meta.categories[0]
  }
  filters.pageNum = 1
  fetchData()
}
const onPageChange = (p: number) => { filters.pageNum = p; fetchData() }
const onSizeChange = (s: number) => { filters.pageSize = s; filters.pageNum = 1; fetchData() }

onMounted(async () => {
  await meta.loadAll()
  await fetchSites()
  loadSavedFilters()
  loadTablePrefs()
  if (filters.site && !sites.value.find(s => s.code === filters.site)) {
    filters.site = sites.value.length ? sites.value[0].code : ''
  }
  if (filters.site) await fetchData()
})
</script>

<style scoped>
.page {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.header-row h2 {
  margin: 0;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
  align-items: center;
}

.meta {
  color: #909399;
  font-size: 13px;
}

.filter-bar {
  margin-bottom: 16px;
}

.filter-bar :deep(.el-form-item) {
  margin-bottom: 4px;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

/* 标题链接样式 */
.link-title {
  color: #409eff;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}
.link-title:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.title-text {
  color: #303133;
}

/* 链接图标 */
.link-icon {
  color: #409eff;
  cursor: pointer;
  font-size: 18px;
  transition: color 0.2s;
}
.link-icon:hover {
  color: #66b1ff;
}
.link-icon-disabled {
  color: #c0c4cc;
  font-size: 18px;
  cursor: not-allowed;
}

/* 封面占位 */
.cover-placeholder {
  width: 40px;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #c0c4cc;
  font-size: 12px;
  border-radius: 2px;
}

/* 简介多行显示 */
.desc-text {
  line-height: 1.5;
}

/* 列设置面板 */
.col-setting {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.col-setting-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
  display: flex;
}

@media (max-width: 768px) {
  .header-row {
    gap: 8px;
  }
  .filter-bar :deep(.el-form-item) {
    margin-right: 8px;
  }
  .filter-bar :deep(.el-select),
  .filter-bar :deep(.el-input) {
    width: 140px !important;
  }
}
</style>
