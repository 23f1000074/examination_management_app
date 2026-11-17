<template>
  <nav class="navbar navbar-expand-md navbar-dark bg-dark">
    <div class="container">
      <span class="navbar-brand">Exam Portal</span>
      <button class="navbar-toggler" type="button" @click="open = !open">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="navbar-collapse" :class="{ collapse: !open }">
        <ul class="navbar-nav me-auto" v-if="user">
          <li class="nav-item" v-for="l in links" :key="l.to">
            <router-link class="nav-link" :to="l.to" @click="open = false">{{ l.text }}</router-link>
          </li>
        </ul>
        <ul class="navbar-nav ms-auto" v-if="user">
          <li class="nav-item">
            <router-link class="nav-link" to="/profile">{{ user.name }}</router-link>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click.prevent="logout">Logout</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>

  <div class="container my-4">
    <router-view />
  </div>
</template>

<script>
import { getUser } from './api.js'

export default {
  data() {
    return { user: getUser(), open: false }
  },
  computed: {
    links() {
      if (!this.user) return []
      if (this.user.role === 'admin') {
        return [
          { to: '/admin', text: 'Dashboard' },
          { to: '/admin/courses', text: 'Courses' },
          { to: '/admin/exams', text: 'Examinations' },
          { to: '/admin/examiners', text: 'Examiners' },
          { to: '/admin/students', text: 'Students' },
          { to: '/admin/slots', text: 'Slots' },
          { to: '/admin/bookings', text: 'Bookings' },
          { to: '/admin/search', text: 'Search' },
        ]
      }
      if (this.user.role === 'examiner') {
        return [
          { to: '/examiner', text: 'Dashboard' },
          { to: '/examiner/slots', text: 'My Slots' },
        ]
      }
      return [
        { to: '/student', text: 'Dashboard' },
        { to: '/student/exams', text: 'Examinations' },
        { to: '/student/bookings', text: 'My Bookings' },
        { to: '/student/results', text: 'Results' },
      ]
    },
  },
  watch: {
    // navbar must refresh after login / logout
    $route() {
      this.user = getUser()
    },
  },
  methods: {
    logout() {
      localStorage.clear()
      this.user = null
      this.$router.push('/login')
    },
  },
}
</script>
