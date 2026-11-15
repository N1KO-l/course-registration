<template>
  <div>
    <div class="page-head">
      <h2>选课</h2>
      <p>COURSE SELECTION</p>
    </div>
    <el-card shadow="never" class="welcome">
      <p class="welcome-text">
        你好，{{ major }} 专业的同学。请从「可选课程」中选择本专业课程（可另选一门公共课和一门体育课）。
        每名学生最多选 <b>5 门</b>课程，且所选课程的上课时间不能冲突；体育/英语不计入学分，总学分不超过 17。
      </p>
    </el-card>

    <el-card shadow="never" class="section-card">
      <template #header>
        已选课程（{{ enrolledCourses.length }}/{{ MAX_COURSES }}）· 已选学分 {{ countedCredits }}/17
      </template>
      <el-table :data="enrolledCourses" border>
        <el-table-column prop="course_code" label="课程号" width="110" />
        <el-table-column prop="name" label="课程" min-width="180" />
        <el-table-column prop="major" label="类别" width="110" />
        <el-table-column prop="credit" label="学分" width="70" />
        <el-table-column prop="teacher" label="教师" width="90" />
        <el-table-column label="上课时间" width="180">
          <template #default="{ row }">{{ courseTime(row) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="onDrop(row)">退课</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" class="section-card">
      <template #header>可选课程（本专业 + 公共课 / 体育 / 英语）</template>
      <el-table :data="availableCourses" border>
        <el-table-column prop="course_code" label="课程号" width="110" />
        <el-table-column prop="name" label="课程" min-width="180" />
        <el-table-column prop="major" label="类别" width="110" />
        <el-table-column prop="credit" label="学分" width="70" />
        <el-table-column prop="teacher" label="教师" width="90" />
        <el-table-column label="上课时间" width="180">
          <template #default="{ row }">{{ courseTime(row) }}</template>
        </el-table-column>
        <el-table-column label="人数" width="80">
          <template #default="{ row }">{{ row.enrolled_count }}/{{ row.capacity }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button size="small" type="primary" :disabled="enrollDisabled(row)" @click="onEnroll(row)">
              {{ enrollLabel(row) }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listCourses } from '../api/courses'
import { listEnrolledCourses, enroll, drop } from '../api/enrollments'

const props = defineProps({
  studentId: { type: Number, default: null },
  major: { type: String, default: '' },
})

const MAX_COURSES = 5
const FREE_ELECTIVE_MAJORS = new Set(['体育', '英语'])
const courses = ref([])
const enrolledCourses = ref([])

const countedCredits = computed(() =>
  enrolledCourses.value.reduce((sum, c) => sum + (FREE_ELECTIVE_MAJORS.has(c.major) ? 0 : c.credit), 0)
)

const availableCourses = computed(() => {
  const selectable = new Set([props.major, '公共课', '体育', '英语'])
  const enrolledIds = new Set(enrolledCourses.value.map((c) => c.id))
  return courses.value.filter((c) => !enrolledIds.has(c.id) && selectable.has(c.major))
})

function courseTime(row) {
  if (!row.day || !row.start_time || !row.end_time) return '待定'
  return `${row.day} ${row.start_time}-${row.end_time}`
}

// 与已选课程同一天且时间区间重叠即视为冲突
function isConflict(row) {
  if (!row.day || !row.start_time || !row.end_time) return false
  return enrolledCourses.value.some(
    (c) =>
      c.day === row.day &&
      c.start_time &&
      c.end_time &&
      row.start_time < c.end_time &&
      c.start_time < row.end_time
  )
}

function enrollDisabled(row) {
  return row.enrolled_count >= row.capacity || enrolledCourses.value.length >= MAX_COURSES || isConflict(row)
}

function enrollLabel(row) {
  if (row.enrolled_count >= row.capacity) return '已满'
  if (enrolledCourses.value.length >= MAX_COURSES) return '已达 5 门'
  if (isConflict(row)) return '时间冲突'
  return '选课'
}

async function loadCourses() {
  const { data } = await listCourses()
  courses.value = data
}

async function loadEnrolled() {
  const { data } = await listEnrolledCourses(props.studentId)
  enrolledCourses.value = data
}

async function onEnroll(row) {
  try {
    await enroll(props.studentId, row.id)
    ElMessage.success('选课成功')
    await Promise.all([loadCourses(), loadEnrolled()])
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '选课失败')
  }
}

async function onDrop(row) {
  try {
    await drop(props.studentId, row.id)
    ElMessage.success('退课成功')
    await Promise.all([loadCourses(), loadEnrolled()])
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '退课失败')
  }
}

onMounted(async () => {
  await Promise.all([loadCourses(), loadEnrolled()])
})
</script>

<style scoped>
.welcome {
  margin-bottom: 16px;
  border-left: 4px solid #bf165e;
}
.welcome-text {
  margin: 0;
  line-height: 1.8;
  color: #606266;
}
.section-card {
  margin-bottom: 16px;
}
</style>
