import http from './http'

export const login = (account, password) => http.post('/auth/login', { account, password })
export const batchRegister = (students) => http.post('/auth/batch-register', { students })
export const importExcel = (formData) => http.post('/auth/import-excel', formData)
export const changePassword = (old_password, new_password) =>
  http.post('/auth/change-password', { old_password, new_password })
