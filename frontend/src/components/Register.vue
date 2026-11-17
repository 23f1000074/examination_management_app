<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <h3 class="mb-3">Student Registration</h3>
      <div class="alert alert-danger" v-if="error">{{ error }}</div>
      <form @submit.prevent="register">
        <div class="mb-3">
          <label class="form-label">Full name</label>
          <input class="form-control" v-model="form.name" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input class="form-control" v-model="form.username" required minlength="3" />
        </div>
        <div class="mb-3">
          <label class="form-label">Email</label>
          <input type="email" class="form-control" v-model="form.email" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Phone</label>
          <input class="form-control" v-model="form.phone" pattern="[0-9]{10}" title="10 digit number" />
        </div>
        <div class="mb-3">
          <label class="form-label">Department</label>
          <input class="form-control" v-model="form.department" />
        </div>
        <div class="mb-3">
          <label class="form-label">Password (min 6 characters)</label>
          <input type="password" class="form-control" v-model="form.password" required minlength="6" />
        </div>
        <button class="btn btn-primary">Register</button>
        <router-link to="/login" class="ms-3">Back to login</router-link>
      </form>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return {
      form: { name: '', username: '', email: '', phone: '', department: '', password: '' },
      error: '',
    }
  },
  methods: {
    async register() {
      this.error = ''
      try {
        await api('/register', 'POST', this.form)
        alert('Registered, please login')
        this.$router.push('/login')
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
