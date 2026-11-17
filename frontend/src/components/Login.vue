<template>
  <div class="row justify-content-center">
    <div class="col-md-5 card card-body mt-4">
      <h3 class="mb-3">Examination Management Portal</h3>
      <div class="alert alert-danger" v-if="error">{{ error }}</div>
      <form @submit.prevent="login">
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input class="form-control" v-model="username" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" class="form-control" v-model="password" required />
        </div>
        <button class="btn btn-primary">Login</button>
        <router-link to="/register" class="ms-3">New student? Register</router-link>
      </form>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { username: '', password: '', error: '' }
  },
  methods: {
    async login() {
      this.error = ''
      try {
        const data = await api('/login', 'POST', { username: this.username, password: this.password })
        localStorage.setItem('token', data.token)
        localStorage.setItem('user', JSON.stringify(data.user))
        this.$router.push('/' + data.user.role)
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
