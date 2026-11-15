<template>
  <div class="login-page">
    <section class="login-brand">
      <img src="/logo-white.png" class="brand-logo" alt="香港城市大学（东莞）" />
      <h1>香港城市大学（东莞）</h1>
      <p class="brand-en">City University of Hong Kong (Dongguan)</p>
      <p class="brand-motto">敬业乐群 · Officium et Civitas</p>
      <p class="brand-slogan">Innovating into the Future</p>
      <div class="brand-divider"></div>
      <p class="system-name">学生选课系统</p>
      <p class="system-en">Student Course Registration System</p>
    </section>

    <section class="login-form-side">
      <div class="login-box">
        <div class="login-head">
          <h2>登录</h2>
          <p>请使用学号 / 邮箱或老师账号登录</p>
        </div>
        <el-form @submit.prevent="onSubmit">
          <el-form-item>
            <el-input v-model="account" placeholder="用户名 / 学号 / 邮箱" size="large" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
              @keyup.enter="onSubmit"
            />
          </el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="onSubmit">
            登录
          </el-button>
        </el-form>
        <p class="hint">老师账号：teacher / teacher123<br />学生用学号或邮箱登录</p>
      </div>
      <div class="login-foot">© 2026 City University of Hong Kong (Dongguan)</div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { login } from '../api/auth'

const emit = defineEmits(['success'])
const account = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!account.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await login(account.value, password.value)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
    localStorage.setItem('student_id', data.student_id ?? '')
    localStorage.setItem('name', data.name ?? data.username)
    localStorage.setItem('major', data.major ?? '')
    ElMessage.success('登录成功')
    emit('success')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: #fff;
}

.login-brand {
  position: relative;
  display: flex;
  flex: 1.05;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  padding: 0 8vw;
  color: #fff;
  background: linear-gradient(135deg, #671e45 0%, #8f1a50 55%, #bf165e 100%);
}
.login-brand::before,
.login-brand::after {
  position: absolute;
  content: '';
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 50%;
}
.login-brand::before {
  top: -120px;
  right: -40px;
  width: 260px;
  height: 260px;
}
.login-brand::after {
  right: -140px;
  bottom: -170px;
  width: 440px;
  height: 440px;
}

.brand-logo {
  align-self: flex-start;
  height: 56px;
  margin-bottom: 40px;
}
.login-brand h1 {
  margin: 0 0 8px;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 2px;
}
.brand-en {
  margin: 0;
  font-size: 14px;
  opacity: 0.85;
}
.brand-motto {
  margin: 28px 0 0;
  font-size: 15px;
  letter-spacing: 3px;
  opacity: 0.92;
}
.brand-slogan {
  margin: 8px 0 0;
  font-size: 13px;
  font-style: italic;
  opacity: 0.7;
}
.brand-divider {
  width: 56px;
  height: 3px;
  margin: 36px 0 24px;
  background: rgba(255, 255, 255, 0.75);
}
.system-name {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 4px;
}
.system-en {
  margin-top: 8px;
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
  opacity: 0.72;
}

.login-form-side {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  background: #fff;
}
.login-box {
  width: 100%;
  max-width: 400px;
}
.login-head h2 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #313131;
}
.login-head p {
  margin: 0 0 30px;
  font-size: 13px;
  color: #909399;
}
.hint {
  margin-top: 22px;
  font-size: 12px;
  line-height: 1.8;
  color: #909399;
  text-align: center;
}
.login-foot {
  position: absolute;
  bottom: 24px;
  font-size: 12px;
  color: #bfbfbf;
}

@media (max-width: 860px) {
  .login-page {
    flex-direction: column;
  }
  .login-brand {
    padding: 48px 32px;
  }
  .brand-logo {
    height: 44px;
    margin-bottom: 24px;
  }
  .login-brand h1 {
    font-size: 26px;
  }
  .login-form-side {
    padding: 40px 24px 80px;
  }
}
</style>
