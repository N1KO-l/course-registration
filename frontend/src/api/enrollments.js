import http from './http'

export const listEnrolledCourses = (studentId) => http.get(`/students/${studentId}/courses`)
export const enroll = (studentId, courseId) => http.post(`/students/${studentId}/courses`, { course_id: courseId })
export const drop = (studentId, courseId) => http.delete(`/students/${studentId}/courses/${courseId}`)
