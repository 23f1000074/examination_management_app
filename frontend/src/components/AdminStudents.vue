<template>
  <h3 class="mb-3">Students</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>
  <div class="table-responsive">
    <table class="table table-bordered">
      <thead><tr><th>Name</th><th>Username</th><th>Email</th><th>Phone</th><th>Department</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="s in students" :key="s.id">
          <td>{{ s.name }}</td><td>{{ s.username }}</td><td>{{ s.email }}</td>
          <td>{{ s.phone }}</td><td>{{ s.department }}</td><td>{{ s.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-secondary" @click="toggle(s)">
              {{ s.status === 'Active' ? 'Deactivate' : 'Activate' }}
            </button>
          </td>
        </tr>
        <tr v-if="!students.length"><td colspan="7">No students registered</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { students: [], error: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.students = await api('/admin/students')
    },
    async toggle(s) {
      const status = s.status === 'Active' ? 'Inactive' : 'Active'
      try {
        await api('/admin/students/' + s.id + '/status', 'PUT', { status: status })
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
