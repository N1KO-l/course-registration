<template>
  <div>
    <div class="page-head">
      <h2>我的课表</h2>
      <p>TIMETABLE</p>
    </div>
    <div class="toolbar">
      <el-button @click="load">刷新</el-button>
      <span class="tip">课表以小时为单位，横轴为星期、纵轴为时刻</span>
    </div>

    <table class="timetable">
      <thead>
        <tr>
          <th class="hour-head">时间</th>
          <th v-for="d in DAYS" :key="d">{{ d }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="hour in HOURS" :key="hour">
          <td class="hour">{{ hour }}:00</td>
          <template v-for="d in DAYS" :key="d">
            <td
              v-if="layout.startsAt[d][hour]"
              :rowspan="layout.rowspan[d][hour]"
              class="cell filled"
            >
              <div class="course-chip">
                <div class="cname">{{ layout.startsAt[d][hour].name }}</div>
                <div class="ctime">
                  {{ layout.startsAt[d][hour].start_time }}-{{ layout.startsAt[d][hour].end_time }}
                </div>
                <div v-if="layout.startsAt[d][hour].weeks" class="cweeks">
                  {{ layout.startsAt[d][hour].weeks }}
                </div>
              </div>
            </td>
            <td v-else-if="!layout.covered[d][hour]" class="cell"></td>
          </template>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listEnrolledCourses } from '../api/enrollments'

const props = defineProps({
  studentId: { type: Number, default: null },
})

const DAYS = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
const HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

const enrolledCourses = ref([])

function startBlock(c) {
  if (!c.start_time) return 0
  return parseInt(c.start_time.split(':')[0], 10)
}
function endBlock(c) {
  if (!c.end_time) return startBlock(c) + 1
  const [h, m] = c.end_time.split(':').map(Number)
  return m > 0 ? h + 1 : h
}
function spanBlocks(c) {
  return Math.max(endBlock(c) - startBlock(c), 1)
}

const layout = computed(() => {
  const startsAt = {}
  const rowspan = {}
  const covered = {}
  for (const d of DAYS) {
    startsAt[d] = {}
    rowspan[d] = {}
    covered[d] = {}
    let skipUntil = -1
    for (const hour of HOURS) {
      if (hour < skipUntil) {
        covered[d][hour] = true
        continue
      }
      const course = enrolledCourses.value.find((c) => c.day === d && startBlock(c) === hour)
      if (course) {
        const span = spanBlocks(course)
        startsAt[d][hour] = course
        rowspan[d][hour] = span
        skipUntil = hour + span
      }
    }
  }
  return { startsAt, rowspan, covered }
})

async function load() {
  try {
    const { data } = await listEnrolledCourses(props.studentId)
    enrolledCourses.value = data
  } catch (e) {
    ElMessage.error('加载失败，请确认后端已启动')
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
.tip {
  color: #909399;
  font-size: 12px;
}
.timetable {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.timetable th,
.timetable td {
  border: 1px solid #f0e3e9;
  text-align: center;
  padding: 0;
  font-size: 12px;
  vertical-align: top;
  height: 56px;
}
.timetable th {
  background: #faf3f6;
  color: #702745;
  height: 40px;
}
.timetable .hour,
.timetable .hour-head {
  width: 70px;
  background: #faf3f6;
  font-weight: bold;
  vertical-align: middle;
}
.cell.filled {
  background: #fbeaf1;
}
.course-chip {
  color: #9f0d43;
  padding: 6px;
  height: 100%;
}
.course-chip .cname {
  font-weight: bold;
}
.course-chip .ctime,
.course-chip .cweeks {
  color: #909399;
  font-size: 11px;
}
</style>
