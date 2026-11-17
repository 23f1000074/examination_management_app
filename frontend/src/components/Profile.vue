<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <h3 class="mb-3">My Profile</h3>
      <div class="alert alert-danger" v-if="error">{{ error }}</div>
      <div class="alert alert-success" v-if="message">{{ message }}</div>
      <form @submit.prevent="save">
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input class="form-control" :value="form.username" disabled />
        </div>
        <div class="mb-3">
          <label class="form-label">Name</label>
          <input class="form-control" v-model="form.name" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Email</label>
          <input type="email" class="form-control" v-model="form.email" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Phone</label>
          <input class="form-control" v-model="form.phone" />
        </div>
        <div class="mb-3">
          <label class="form-label">Department</label>
          <input class="form-control" v-model="form.department" />
        </div>
        <div class="mb-3">
          <label class="form-label">New password (leave empty to keep old one)</label>
          <input type="password" class="form-control" v-model="form.password" minlength="6" />
        </div>
        <button class="btn btn-primary">Save</button>
      </form>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { form: {}, error: '', message: '' }
  },
  async mounted() {
    this.form = await api('/profile')
  },
  methods: {
    async save() {
      this.error = ''
      this.message = ''
      try {
        const data = await api('/profile', 'PUT', this.form)
        localStorage.setItem('user', JSON.stringify(data.user))
        this.message = data.message
        this.form.password = ''
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
