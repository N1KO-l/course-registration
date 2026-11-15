<template>
  <div>
    <div class="page-head">
      <h2>学生管理</h2>
      <p>STUDENTS</p>
    </div>
    <div class="toolbar">
      <el-button type="primary" @click="batchDialogVisible = true">批量注册学生</el-button>
      <el-upload
        action="#"
        :http-request="doImport"
        :show-file-list="false"
        accept=".xlsx,.xls"
        style="display: inline-block; margin-left: 12px"
      >
        <el-button type="success">Excel 导入</el-button>
      </el-upload>
      <el-button
        type="danger"
        :disabled="selected.length === 0"
        style="margin-left: 12px"
        @click="onBatchDelete"
      >
        批量删除{{ selected.length ? `（${selected.length}）` : '' }}
      </el-button>
      <el-input
        v-model="keyword"
        placeholder="搜索姓名 / 学号 / 专业"
        clearable
        style="width: 240px; margin-left: 12px"
        @keyup.enter="search"
        @clear="search"
      />
      <el-button @click="search" style="margin-left: 8px">搜索</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-table :data="students" v-loading="loading" border stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="45" />
      <el-table-column prop="id" label="ID" width="55" />
      <el-table-column prop="student_no" label="学号" width="125" />
      <el-table-column prop="name" label="姓名" width="110" />
      <el-table-column prop="gender" label="性别" width="60" />
      <el-table-column prop="grade" label="年级" width="70" />
      <el-table-column prop="major" label="专业" width="130" />
      <el-table-column prop="major_code" label="专业代码" width="90" />
      <el-table-column prop="age" label="年龄" width="60" />
      <el-table-column prop="email" label="邮箱" min-width="150" />
      <el-table-column prop="id_card" label="身份证号" min-width="180" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="warning" @click="openReset(row)">重置密码</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="load"
        @size-change="onSizeChange"
      />
    </div>

    <!-- 批量注册 -->
    <el-dialog v-model="batchDialogVisible" title="批量注册学生" width="580px">
      <p class="hint-text">
        每行一个学生，格式：<b>姓名,年级,专业,年龄,性别,身份证号</b><br />
        学号自动生成（年级+专业代码+随机三位），邮箱自动为「学号@1.com」，初始密码为 123456
      </p>
      <el-input
        v-model="batchText"
        type="textarea"
        :rows="10"
        placeholder="张三,2022,数据科学,22,男,11010120000101001X&#10;李四,2022,数据科学,21,女,110101200001010021"
      />
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onBatchImport">解析并导入</el-button>
      </template>
    </el-dialog>

    <!-- 编辑 -->
    <el-dialog v-model="dialogVisible" title="编辑学生" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="学号">
          <el-input v-model="form.student_no" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" placeholder="选择性别" style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="1" :max="120" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="form.grade" placeholder="如 2022" />
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="form.major" filterable style="width: 100%" @change="onMajorChange">
            <el-option v-for="(code, name) in MAJOR_CODES" :key="code" :label="name" :value="name" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业代码">
          <el-input v-model="form.major_code" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.id_card" maxlength="18" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" width="400px">
      <p class="hint-text">为学生「{{ resetTarget?.name }}」设置新密码：</p>
      <el-form label-width="80px">
        <el-form-item label="新密码">
          <el-input v-model="resetPwd" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onResetPwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listStudents, updateStudent, deleteStudent, resetPassword, batchDeleteStudents } from '../api/students'
import { batchRegister, importExcel } from '../api/auth'

// 与后端 app/majors.py 保持一致；编辑学生时专业名称与代码联动
const MAJOR_CODES = {
  工程管理: '010',
  电子电气工程: '011',
  电子信息工程: '012',
  数据科学: '013',
  计算机科学: '014',
  人工智能: '015',
  材料工程与纳米技术: '016',
  生物医学工程: '017',
  商业数据分析: '018',
  商业信息系统: '019',
  创业管理: '020',
}

function onMajorChange(name) {
  form.value.major_code = MAJOR_CODES[name] || ''
}

const students = ref([])
const loading = ref(false)
const selected = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const keyword = ref('')

const dialogVisible = ref(false)
const batchDialogVisible = ref(false)
const resetDialogVisible = ref(false)
const batchText = ref('')
const resetTarget = ref(null)
const resetPwd = ref('')
const form = ref({ id: null, student_no: '', name: '', gender: '', age: 0, grade: '', major: '', major_code: '', email: '', id_card: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await listStudents({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    students.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error('加载失败，请确认后端已启动')
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function onSizeChange(size) {
  pageSize.value = size
  page.value = 1
  load()
}

function openEdit(row) {
  form.value = { ...row }
  dialogVisible.value = true
}

async function onSubmit() {
  try {
    await updateStudent(form.value.id, form.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

function openReset(row) {
  resetTarget.value = row
  resetPwd.value = ''
  resetDialogVisible.value = true
}

async function onResetPwd() {
  if (!resetPwd.value) {
    ElMessage.warning('请输入新密码')
    return
  }
  try {
    await resetPassword(resetTarget.value.id, resetPwd.value)
    ElMessage.success('密码已重置')
    resetDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '重置失败')
  }
}

function handleSelectionChange(rows) {
  selected.value = rows
}

async function onBatchDelete() {
  if (!selected.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.value.length} 名学生吗？其登录账号也会被删除。`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    const { data } = await batchDeleteStudents(selected.value.map((s) => s.id))
    ElMessage.success(`已删除 ${data.deleted_count} 名学生`)
    selected.value = []
    load()
  } catch (e) {
    ElMessage.error('批量删除失败')
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除学生「${row.name}」吗？其登录账号也会被删除。`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteStudent(row.id)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function parseLines(text) {
  return text
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .map((line) => {
      const p = line.split(/[,，\t]+/).map((s) => s.trim())
      return {
        name: p[0] || '',
        grade: p[1] || '',
        major: p[2] || '',
        age: p[3] ? parseInt(p[3], 10) || 0 : 0,
        gender: p[4] || '',
        id_card: p[5] || '',
      }
    })
}

async function doImport({ file }) {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const { data } = await importExcel(formData)
    ElMessage.success(`成功导入 ${data.created_count} 人`)
    if (data.skipped && data.skipped.length) {
      ElMessage.warning(`有 ${data.skipped.length} 人被跳过（缺少信息或专业代码不存在）`)
    }
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  }
}

async function onBatchImport() {
  const list = parseLines(batchText.value)
  if (!list.length) {
    ElMessage.warning('请先粘贴学生数据')
    return
  }
  try {
    const { data } = await batchRegister(list)
    ElMessage.success(`成功注册 ${data.created_count} 人`)
    if (data.skipped && data.skipped.length) {
      ElMessage.warning(`有 ${data.skipped.length} 人被跳过（缺少信息或专业代码不存在）`)
    }
    batchDialogVisible.value = false
    batchText.value = ''
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '批量注册失败')
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
.hint-text {
  color: #909399;
  font-size: 13px;
  line-height: 1.8;
}
</style>
