<template>
  <h3 class="mb-3">Courses</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <form class="row g-2 mb-4" @submit.prevent="save">
    <div class="col-md-2">
      <input class="form-control" placeholder="Code" v-model="form.code" required />
    </div>
    <div class="col-md-3">
      <input class="form-control" placeholder="Course name" v-model="form.name" required />
    </div>
    <div class="col-md-4">
      <input class="form-control" placeholder="Description" v-model="form.description" />
    </div>
    <div class="col-md-1">
      <select class="form-select" v-model="form.status">
        <option>Active</option>
        <option>Inactive</option>
      </select>
    </div>
    <div class="col-md-2">
      <button class="btn btn-primary">{{ editId ? 'Update' : 'Add' }}</button>
      <button type="button" class="btn btn-secondary ms-1" v-if="editId" @click="reset">Cancel</button>
    </div>
  </form>

  <div class="table-responsive">
    <table class="table table-bordered">
      <thead><tr><th>Code</th><th>Name</th><th>Description</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="c in courses" :key="c.id">
          <td>{{ c.code }}</td>
          <td>{{ c.name }}</td>
          <td>{{ c.description }}</td>
          <td>{{ c.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary me-1" @click="edit(c)">Edit</button>
            <button class="btn btn-sm btn-outline-danger" @click="remove(c)">Delete</button>
          </td>
        </tr>
        <tr v-if="!courses.length"><td colspan="5">No courses yet</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return {
      courses: [],
      form: { code: '', name: '', description: '', status: 'Active' },
      editId: null,
      error: '',
    }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.courses = await api('/admin/courses')
    },
    async save() {
      this.error = ''
      try {
        if (this.editId) {
          await api('/admin/courses/' + this.editId, 'PUT', this.form)
        } else {
          await api('/admin/courses', 'POST', this.form)
        }
        this.reset()
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    edit(c) {
      this.editId = c.id
      this.form = { code: c.code, name: c.name, description: c.description, status: c.status }
    },
    reset() {
      this.editId = null
      this.form = { code: '', name: '', description: '', status: 'Active' }
    },
    async remove(c) {
      if (!confirm('Delete course ' + c.code + '?')) return
      try {
        await api('/admin/courses/' + c.id, 'DELETE')
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
