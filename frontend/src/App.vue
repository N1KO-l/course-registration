<template>
  <Login v-if="!isLoggedIn" @success="onLoginSuccess" />

  <el-container v-else class="layout">
    <div class="top-bar"></div>
    <el-header class="header">
      <div class="header-inner">
        <img src="/logo-header-official.png" class="logo" alt="香港城市大学（东莞）" />
        <div class="brand-text">
          <div class="app-title">学生选课系统</div>
          <div class="app-subtitle">Course Registration System</div>
        </div>
        <div class="spacer"></div>
        <div class="user-box">
          <span class="username">{{ name }}</span>
          <span class="role-tag">{{ role === 'teacher' ? '老师' : '学生' }}</span>
        </div>
        <el-button class="header-btn" text @click="openPwdDialog">修改密码</el-button>
        <el-button class="header-btn" text @click="logout">退出登录</el-button>
      </div>
    </el-header>
    <el-main class="main">
      <div class="content">
        <el-tabs v-if="role === 'teacher'" v-model="activeTab" class="nav-tabs">
          <el-tab-pane label="学生管理" name="students">
            <Students />
          </el-tab-pane>
          <el-tab-pane label="课程管理" name="courses">
            <Courses />
          </el-tab-pane>
          <el-tab-pane label="选课/退课" name="enrollments">
            <Enrollments />
          </el-tab-pane>
        </el-tabs>
        <el-tabs v-else v-model="studentTab" class="nav-tabs">
          <el-tab-pane label="选课" name="enroll" lazy>
            <StudentEnroll :student-id="studentId" :major="major" />
          </el-tab-pane>
          <el-tab-pane label="我的课表" name="timetable" lazy>
            <StudentTimetable :student-id="studentId" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-main>
    <el-footer class="footer">
      <div class="footer-inner">
        <img src="/logo-white.png" class="footer-logo" alt="City University of Hong Kong (Dongguan)" />
        <div class="footer-text">
          <div class="footer-title">香港城市大学（东莞） · 学生选课系统</div>
          <div class="footer-sub">敬业乐群 · Officium et Civitas · Innovating into the Future</div>
        </div>
        <div class="footer-right">© 2026 City University of Hong Kong (Dongguan)</div>
      </div>
    </el-footer>
  </el-container>

  <el-dialog v-model="pwdDialogVisible" title="修改密码" width="400px">
    <el-form label-width="90px">
      <el-form-item label="原密码">
        <el-input v-model="oldPwd" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="newPwd" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="confirmPwd" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitPwd">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import Students from './views/Students.vue'
import Courses from './views/Courses.vue'
import Enrollments from './views/Enrollments.vue'
import StudentEnroll from './views/StudentEnroll.vue'
import StudentTimetable from './views/StudentTimetable.vue'
import Login from './views/Login.vue'
import { changePassword } from './api/auth'

const activeTab = ref('students')
const studentTab = ref('enroll')
const isLoggedIn = ref(!!localStorage.getItem('token'))
const role = ref(localStorage.getItem('role') || 'student')
const name = ref(localStorage.getItem('name') || localStorage.getItem('username') || '')
const studentId = ref(getStudentId())
const major = ref(localStorage.getItem('major') || '')

const pwdDialogVisible = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')

function getStudentId() {
  const v = localStorage.getItem('student_id')
  return v ? Number(v) : null
}

function onLoginSuccess() {
  isLoggedIn.value = true
  role.value = localStorage.getItem('role') || 'student'
  name.value = localStorage.getItem('name') || localStorage.getItem('username') || ''
  studentId.value = getStudentId()
  major.value = localStorage.getItem('major') || ''
}

function logout() {
  ;['token', 'username', 'role', 'student_id', 'name', 'major'].forEach((k) => localStorage.removeItem(k))
  isLoggedIn.value = false
}

function openPwdDialog() {
  oldPwd.value = ''
  newPwd.value = ''
  confirmPwd.value = ''
  pwdDialogVisible.value = true
}

async function submitPwd() {
  if (!oldPwd.value || !newPwd.value) {
    ElMessage.warning('请输入原密码和新密码')
    return
  }
  if (newPwd.value !== confirmPwd.value) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  try {
    await changePassword(oldPwd.value, newPwd.value)
    ElMessage.success('密码修改成功')
    pwdDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  }
}
</script>

<style>
:root {
  --el-color-primary: #bf165e;
  --el-color-primary-light-3: #d15a8a;
  --el-color-primary-light-5: #e08cae;
  --el-color-primary-light-7: #efbdd2;
  --el-color-primary-light-8: #f5d3e1;
  --el-color-primary-light-9: #fbeaf1;
  --el-color-primary-dark-2: #9f0d43;
  --el-border-radius-base: 6px;
  --el-table-header-bg-color: #faf3f6;
  --el-table-header-text-color: #702745;
  --el-table-row-hover-bg-color: #fdf5f8;
  --el-font-family: Lato, 'PingFang SC', 'PingFang HK', 'Microsoft YaHei', Arial, sans-serif;
}

* {
  box-sizing: border-box;
}
body {
  margin: 0;
  background: #f5f5f5;
  color: #313131;
  font-family: var(--el-font-family);
  -webkit-font-smoothing: antialiased;
}

.layout {
  min-height: 100vh;
}
.top-bar {
  height: 4px;
  background: linear-gradient(90deg, #671e45, #bf165e);
}
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 76px;
  padding: 0;
  background: #fff;
  box-shadow: 0 1px 20px -6px rgba(0, 0, 0, 0.18);
}
.header-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  max-width: 1280px;
  height: 100%;
  margin: 0 auto;
  padding: 0 24px;
}
.logo {
  height: 44px;
}
.brand-text {
  padding-left: 16px;
  border-left: 1px solid #e8e8e8;
}
.app-title {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
  color: #313131;
}
.app-subtitle {
  margin-top: 2px;
  font-size: 11px;
  color: #bf165e;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.spacer {
  flex: 1;
}
.user-box {
  display: flex;
  align-items: center;
  gap: 8px;
}
.username {
  font-weight: 600;
  color: #313131;
}
.role-tag {
  padding: 2px 10px;
  font-size: 12px;
  color: #bf165e;
  background: #fbeaf1;
  border-radius: 999px;
}
.header-btn {
  color: #702745;
}
.header-btn:hover {
  color: #bf165e;
  background: #faf3f6;
}

.main {
  padding: 0;
  background: #f5f5f5;
}
.content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px 24px 40px;
}

/* 顶部导航：模仿官网的白底 + 红色下划线 */
.nav-tabs > .el-tabs__header {
  margin: 0 0 18px;
}
.nav-tabs .el-tabs__nav-wrap::after {
  height: 1px;
  background: #e8e8e8;
}
.nav-tabs .el-tabs__item {
  height: 52px;
  padding: 0 26px;
  font-size: 16px;
  font-weight: 600;
  line-height: 52px;
  color: #702745;
}
.nav-tabs .el-tabs__item:hover {
  color: #bf165e;
}
.nav-tabs .el-tabs__item.is-active {
  color: #bf165e;
}
.nav-tabs .el-tabs__active-bar {
  height: 3px;
  background: #bf165e;
  border-radius: 3px;
}
.nav-tabs .el-tabs__content {
  padding-top: 4px;
}

.footer {
  height: auto;
  margin-top: auto;
  padding: 26px 0 20px;
  color: #fff;
  background: linear-gradient(90deg, #671e45 0%, #8f1a50 55%, #bf165e 100%);
}
.footer-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}
.footer-logo {
  height: 38px;
}
.footer-title {
  font-size: 15px;
  font-weight: 700;
}
.footer-sub {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.82;
}
.footer-right {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.75;
}

/* 页面小标题：模仿官网栏目标题 */
.page-head {
  margin: 0 0 16px;
}
.page-head h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #313131;
}
.page-head p {
  margin: 4px 0 0;
  font-size: 11px;
  font-weight: 600;
  color: #bf165e;
  letter-spacing: 2px;
}

.el-card {
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
.el-card__header {
  font-weight: 700;
  color: #313131;
  border-bottom: 1px solid #f3e6ec;
}
.el-table {
  border-radius: 8px;
}
.el-button--primary {
  --el-button-bg-color: #bf165e;
  --el-button-border-color: #bf165e;
  --el-button-hover-bg-color: #9f0d43;
  --el-button-hover-border-color: #9f0d43;
  --el-button-active-bg-color: #8f0b3c;
  --el-button-active-border-color: #8f0b3c;
}
</style>
