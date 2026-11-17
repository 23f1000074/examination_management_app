import { createRouter, createWebHistory } from 'vue-router'
import { getUser } from './api.js'

import Login from './components/Login.vue'
import Register from './components/Register.vue'
import Profile from './components/Profile.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AdminCourses from './components/AdminCourses.vue'
import AdminExams from './components/AdminExams.vue'
import AdminExaminers from './components/AdminExaminers.vue'
import AdminStudents from './components/AdminStudents.vue'
import AdminSlots from './components/AdminSlots.vue'
import AdminBookings from './components/AdminBookings.vue'
import AdminSearch from './components/AdminSearch.vue'
import ExaminerDashboard from './components/ExaminerDashboard.vue'
import ExaminerSlots from './components/ExaminerSlots.vue'
import ExaminerEvaluate from './components/ExaminerEvaluate.vue'
import StudentDashboard from './components/StudentDashboard.vue'
import StudentExams from './components/StudentExams.vue'
import StudentBookings from './components/StudentBookings.vue'
import StudentResults from './components/StudentResults.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/profile', component: Profile, meta: { role: 'any' } },

  { path: '/admin', component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/courses', component: AdminCourses, meta: { role: 'admin' } },
  { path: '/admin/exams', component: AdminExams, meta: { role: 'admin' } },
  { path: '/admin/examiners', component: AdminExaminers, meta: { role: 'admin' } },
  { path: '/admin/students', component: AdminStudents, meta: { role: 'admin' } },
  { path: '/admin/slots', component: AdminSlots, meta: { role: 'admin' } },
  { path: '/admin/bookings', component: AdminBookings, meta: { role: 'admin' } },
  { path: '/admin/search', component: AdminSearch, meta: { role: 'admin' } },

  { path: '/examiner', component: ExaminerDashboard, meta: { role: 'examiner' } },
  { path: '/examiner/slots', component: ExaminerSlots, meta: { role: 'examiner' } },
  { path: '/examiner/evaluate/:id', component: ExaminerEvaluate, meta: { role: 'examiner' } },

  { path: '/student', component: StudentDashboard, meta: { role: 'student' } },
  { path: '/student/exams', component: StudentExams, meta: { role: 'student' } },
  { path: '/student/bookings', component: StudentBookings, meta: { role: 'student' } },
  { path: '/student/results', component: StudentResults, meta: { role: 'student' } },
]

const router = createRouter({ history: createWebHistory(), routes })

// block pages the user is not allowed to open
router.beforeEach((to) => {
  const needed = to.meta.role
  if (!needed) return true
  const user = getUser()
  if (!user) return '/login'
  if (needed !== 'any' && user.role !== needed) return '/' + user.role
  return true
})

export default router
