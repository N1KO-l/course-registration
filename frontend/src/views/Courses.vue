<template>
  <div>
    <div class="page-head">
      <h2>课程管理</h2>
      <p>COURSES</p>
    </div>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新增课程</el-button>
      <el-button @click="load">刷新</el-button>
      <el-input
        v-model="keyword"
        placeholder="搜索课程名称 / 代码"
        clearable
        style="width: 220px; margin-left: 12px"
      />
      <el-select
        v-model="majorFilter"
        placeholder="按专业筛选"
        clearable
        filterable
        style="width: 180px; margin-left: 12px"
      >
        <el-option v-for="m in majors" :key="m" :label="m" :value="m" />
      </el-select>
    </div>

    <el-table :data="pagedCourses" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="course_code" label="课程代码" width="110" />
      <el-table-column prop="name" label="课程名称" min-width="190" />
      <el-table-column prop="major" label="专业" width="150" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column prop="teacher" label="教师" width="110" />
      <el-table-column label="上课时间" width="200">
        <template #default="{ row }">
          <span v-if="row.day">{{ row.day }} {{ row.start_time }}-{{ row.end_time }}</span>
          <span v-else>未安排</span>
        </template>
      </el-table-column>
      <el-table-column label="选课人数" width="110">
        <template #default="{ row }">
          {{ row.enrolled_count }} / {{ row.capacity }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="filteredCourses.length"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="onSizeChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑课程' : '新增课程'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="课程代码">
          <el-input v-model="form.course_code" placeholder="如 DSC5001" />
        </el-form-item>
        <el-form-item label="课程名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="form.major" filterable allow-create placeholder="请选择或输入专业" style="width: 100%">
            <el-option v-for="m in majors" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="学分">
          <el-input-number v-model="form.credit" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="容量">
          <el-input-number v-model="form.capacity" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="教师">
          <el-input v-model="form.teacher" />
        </el-form-item>
        <el-form-item label="星期">
          <el-select v-model="form.day" placeholder="选择星期" clearable style="width: 100%">
            <el-option v-for="d in DAY_OPTIONS" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="上课时间">
          <el-time-picker v-model="form.start_time" format="HH:mm" value-format="HH:mm" placeholder="开始" style="width: 45%" />
          <span style="margin: 0 6px">—</span>
          <el-time-picker v-model="form.end_time" format="HH:mm" value-format="HH:mm" placeholder="结束" style="width: 45%" />
          <span class="time-hint">单次课程固定 2 小时</span>
        </el-form-item>
        <el-form-item label="周次">
          <el-input v-model="form.weeks" placeholder="如 第1-13周" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listCourses, createCourse, updateCourse, deleteCourse } from '../api/courses'

const courses = ref([])
const loading = ref(false)
const keyword = ref('')
const majorFilter = ref('')
const page = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const DAY_OPTIONS = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
const form = ref({ id: null, course_code: '', name: '', credit: 3, capacity: 50, teacher: '', major: '', day: '', period: '', start_time: '', end_time: '', weeks: '' })

const majors = computed(() => [...new Set(courses.value.map((c) => c.major).filter(Boolean))])

const filteredCourses = computed(() => {
  let list = courses.value
  if (majorFilter.value) {
    list = list.filter((c) => c.major === majorFilter.value)
  }
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(
      (c) => c.name.toLowerCase().includes(kw) || c.course_code.toLowerCase().includes(kw)
    )
  }
  return list
})

const pagedCourses = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredCourses.value.slice(start, start + pageSize.value)
})

watch([keyword, majorFilter], () => {
  page.value = 1
})

function onSizeChange(size) {
  pageSize.value = size
  page.value = 1
}

async function load() {
  loading.value = true
  try {
    const { data } = await listCourses()
    courses.value = data
  } catch (e) {
    ElMessage.error('加载失败，请确认后端已启动')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { id: null, course_code: '', name: '', credit: 3, capacity: 50, teacher: '', major: '', day: '', period: '', start_time: '', end_time: '', weeks: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  form.value = { ...row }
  dialogVisible.value = true
}

async function onSubmit() {
  try {
    if (form.value.id) {
      await updateCourse(form.value.id, form.value)
    } else {
      await createCourse(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除课程「${row.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteCourse(row.id)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.time-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
