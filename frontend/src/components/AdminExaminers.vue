<template>
  <h3 class="mb-3">Examiners</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <form class="card card-body mb-4" @submit.prevent="save">
    <h5>{{ editId ? 'Edit examiner' : 'Add examiner' }}</h5>
    <div class="row g-2">
      <div class="col-md-4"><input class="form-control" placeholder="Name" v-model="form.name" required /></div>
      <div class="col-md-4">
        <input class="form-control" placeholder="Username" v-model="form.username" :disabled="editId" required />
      </div>
      <div class="col-md-4"><input type="email" class="form-control" placeholder="Email" v-model="form.email" required /></div>
      <div class="col-md-3"><input class="form-control" placeholder="Phone" v-model="form.phone" /></div>
      <div class="col-md-3"><input class="form-control" placeholder="Department" v-model="form.department" /></div>
      <div class="col-md-3">
        <input type="password" class="form-control" minlength="6"
               :placeholder="editId ? 'New password (optional)' : 'Password'" v-model="form.password" :required="!editId" />
      </div>
      <div class="col-md-3" v-if="editId">
        <select class="form-select" v-model="form.status">
          <option>Active</option>
          <option>Inactive</option>
        </select>
      </div>
    </div>
    <div class="mt-3">
      <button class="btn btn-primary">{{ editId ? 'Update' : 'Add' }}</button>
      <button type="button" class="btn btn-secondary ms-2" v-if="editId" @click="reset">Cancel</button>
    </div>
  </form>

  <div class="table-responsive">
    <table class="table table-bordered">
      <thead><tr><th>Name</th><th>Username</th><th>Email</th><th>Phone</th><th>Department</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="x in examiners" :key="x.id">
          <td>{{ x.name }}</td><td>{{ x.username }}</td><td>{{ x.email }}</td>
          <td>{{ x.phone }}</td><td>{{ x.department }}</td><td>{{ x.status }}</td>
          <td><button class="btn btn-sm btn-outline-primary" @click="edit(x)">Edit</button></td>
        </tr>
        <tr v-if="!examiners.length"><td colspan="7">No examiners yet</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

const emptyForm = () => ({ name: '', username: '', email: '', phone: '', department: '', password: '', status: 'Active' })

export default {
  data() {
    return { examiners: [], form: emptyForm(), editId: null, error: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.examiners = await api('/admin/examiners')
    },
    async save() {
      this.error = ''
      try {
        if (this.editId) {
          await api('/admin/examiners/' + this.editId, 'PUT', this.form)
        } else {
          await api('/admin/examiners', 'POST', this.form)
        }
        this.reset()
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    edit(x) {
      this.editId = x.id
      this.form = { name: x.name, username: x.username, email: x.email, phone: x.phone,
                    department: x.department, password: '', status: x.status }
      window.scrollTo(0, 0)
    },
    reset() {
      this.editId = null
      this.form = emptyForm()
    },
  },
}
</script>
