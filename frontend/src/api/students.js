import http from './http'

export const listStudents = (params = {}) => http.get('/students/', { params })
export const createStudent = (data) => http.post('/students/', data)
export const updateStudent = (id, data) => http.put(`/students/${id}`, data)
export const deleteStudent = (id) => http.delete(`/students/${id}`)
export const batchDeleteStudents = (ids) => http.post('/students/batch-delete', { ids })
export const resetPassword = (id, new_password) => http.post(`/students/${id}/reset-password`, { new_password })
