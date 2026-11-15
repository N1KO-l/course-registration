import http from './http'

export const listCourses = () => http.get('/courses/')
export const createCourse = (data) => http.post('/courses/', data)
export const updateCourse = (id, data) => http.put(`/courses/${id}`, data)
export const deleteCourse = (id) => http.delete(`/courses/${id}`)
