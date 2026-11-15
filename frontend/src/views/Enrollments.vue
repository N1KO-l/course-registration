<template>
  <div>
    <div class="page-head">
      <h2>选课与退课</h2>
      <p>ENROLLMENTS</p>
    </div>
    <div class="toolbar">
      <span class="label">选择学生：</span>
      <el-select
        v-model="studentId"
        placeholder="请选择学生（可输入学号搜索）"
        filterable
        style="width: 260px"
        @change="loadEnrolled"
      >
        <el-option v-for="s in students" :key="s.id" :label="`${s.name}（${s.student_no}）`" :value="s.id" />
      </el-select>
      <span class="label filter-label">专业筛选：</span>
      <el-select v-model="majorFilter" placeholder="全部专业" clearable filterable style="width: 180px">
        <el-option v-for="m in majors" :key="m" :label="m" :value="m" />
      </el-select>
      <el-button style="margin-left: 12px" @click="refresh">刷新</el-button>
    </div>

    <div v-if="!studentId" class="tip">请先在上方选择一个学生</div>

    <el-row v-else :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>已选课程（{{ filteredEnrolled.length }}）· 已选学分 {{ countedCredits }}/17</template>
          <el-table :data="filteredEnrolled" border>
            <el-table-column prop="course_code" label="课程号" width="110" />
            <el-table-column prop="name" label="课程" min-width="160" />
            <el-table-column prop="major" label="专业" width="120" />
            <el-table-column prop="credit" label="学分" width="70" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="onDrop(row)">退课</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>可选课程</template>
          <el-table :data="availableCourses" border>
            <el-table-column prop="course_code" label="课程号" width="110" />
            <el-table-column prop="name" label="课程" min-width="160" />
            <el-table-column prop="major" label="专业" width="120" />
            <el-table-column prop="credit" label="学分" width="70" />
            <el-table-column label="人数" width="80">
              <template #default="{ row }">
                {{ row.enrolled_count }}/{{ row.capacity }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="primary"
                  :disabled="row.enrolled_count >= row.capacity"
                  @click="onEnroll(row)"
                >
                  {{ row.enrolled_count >= row.capacity ? '已满' : '选课' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listStudents } from '../api/students'
import { listCourses } from '../api/courses'
import { listEnrolledCourses, enroll, drop } from '../api/enrollments'

const students = ref([])
const courses = ref([])
const enrolledCourses = ref([])
const studentId = ref(null)
const majorFilter = ref('')

const majors = computed(() => [...new Set(courses.value.map((c) => c.major).filter(Boolean))])
const FREE_ELECTIVE_MAJORS = new Set(['体育', '英语'])
const countedCredits = computed(() =>
  enrolledCourses.value.reduce((sum, c) => sum + (FREE_ELECTIVE_MAJORS.has(c.major) ? 0 : c.credit), 0)
)

const filteredEnrolled = computed(() => {
  if (!majorFilter.value) return enrolledCourses.value
  return enrolledCourses.value.filter((c) => c.major === majorFilter.value)
})

const availableCourses = computed(() => {
  const enrolledIds = new Set(enrolledCourses.value.map((c) => c.id))
  return courses.value.filter((c) => {
    if (enrolledIds.has(c.id)) return false
    if (majorFilter.value && c.major !== majorFilter.value) return false
    return true
  })
})

async function loadStudents() {
  const { data } = await listStudents({ page: 1, page_size: 10000 })
  students.value = data.items
}

async function loadCourses() {
  const { data } = await listCourses()
  courses.value = data
}

async function loadEnrolled() {
  if (!studentId.value) return
  const { data } = await listEnrolledCourses(studentId.value)
  enrolledCourses.value = data
}

async function refresh() {
  await Promise.all([loadStudents(), loadCourses()])
  if (studentId.value) {
    await loadEnrolled()
  }
  ElMessage.success('已刷新')
}

async function onEnroll(row) {
  try {
    await enroll(studentId.value, row.id)
    ElMessage.success('选课成功')
    await Promise.all([loadCourses(), loadEnrolled()])
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '选课失败')
  }
}

async function onDrop(row) {
  try {
    await drop(studentId.value, row.id)
    ElMessage.success('退课成功')
    await Promise.all([loadCourses(), loadEnrolled()])
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '退课失败')
  }
}

onMounted(async () => {
  await Promise.all([loadStudents(), loadCourses()])
})
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
.label {
  font-weight: bold;
  margin-right: 4px;
}
.filter-label {
  margin-left: 20px;
}
.tip {
  color: #909399;
  padding: 40px 0;
  text-align: center;
}
</style>
