<template>
  <h3 class="mb-3">My Slots</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <form class="card card-body mb-4" @submit.prevent="save">
    <h5>{{ editId ? 'Update slot' : 'Create slot' }}</h5>
    <div class="row g-2">
      <div class="col-md-4">
        <select class="form-select" v-model="form.exam_id" :disabled="editId" required>
          <option value="" disabled>Select examination</option>
          <option v-for="e in openExams" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </div>
      <div class="col-md-2"><input type="date" class="form-control" v-model="form.date" required /></div>
      <div class="col-md-2"><input type="time" class="form-control" v-model="form.start_time" required /></div>
      <div class="col-md-2"><input type="time" class="form-control" v-model="form.end_time" required /></div>
      <div class="col-md-2"><input type="number" min="1" class="form-control" placeholder="Capacity" v-model="form.capacity" required /></div>
    </div>
    <div class="mt-3">
      <button class="btn btn-primary">{{ editId ? 'Update' : 'Create' }}</button>
      <button type="button" class="btn btn-secondary ms-2" v-if="editId" @click="reset">Cancel</button>
      <small class="text-muted ms-3" v-if="!openExams.length">Slot creation is not open for any of your examinations.</small>
    </div>
  </form>

  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead><tr><th>Examination</th><th>Date</th><th>Time</th><th>Seats left</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>
        <tr v-for="s in slots" :key="s.id">
          <td>{{ s.exam_name }}</td>
          <td>{{ s.date }}</td>
          <td>{{ s.start_time }} - {{ s.end_time }}</td>
          <td>{{ s.available_seats }} / {{ s.capacity }}</td>
          <td>{{ s.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-secondary me-1" @click="showStudents(s)">Students</button>
            <button class="btn btn-sm btn-outline-primary me-1" @click="edit(s)">Edit</button>
            <button class="btn btn-sm btn-outline-danger" @click="remove(s)">Delete</button>
          </td>
        </tr>
        <tr v-if="!slots.length"><td colspan="6">No slots yet</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card card-body" v-if="viewing">
    <h5>Students booked for {{ viewing.exam_name }} on {{ viewing.date }} {{ viewing.start_time }}</h5>
    <table class="table table-sm">
      <thead><tr><th>Student</th><th>Booking status</th><th>Evaluation</th><th></th></tr></thead>
      <tbody>
        <tr v-for="b in students" :key="b.id">
          <td>{{ b.student_name }}</td>
          <td>{{ b.status }}</td>
          <td>{{ b.evaluated ? 'Done' : 'Pending' }}</td>
          <td><router-link class="btn btn-sm btn-primary" :to="'/examiner/evaluate/' + b.id">{{ b.evaluated ? 'Edit marks' : 'Evaluate' }}</router-link></td>
        </tr>
        <tr v-if="!students.length"><td colspan="4">No students booked</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

const emptyForm = () => ({ exam_id: '', date: '', start_time: '', end_time: '', capacity: '' })

export default {
  data() {
    return { slots: [], exams: [], form: emptyForm(), editId: null, error: '', viewing: null, students: [] }
  },
  computed: {
    // only exams where slot creation is open can get new slots
    openExams() {
      return this.exams.filter((e) => e.status === 'Slot Creation')
    },
  },
  async mounted() {
    const d = await api('/examiner/dashboard')
    this.exams = d.exams
    this.load()
  },
  methods: {
    async load() {
      this.slots = await api('/examiner/slots')
    },
    async save() {
      this.error = ''
      try {
        if (this.editId) {
          await api('/examiner/slots/' + this.editId, 'PUT', this.form)
        } else {
          await api('/examiner/slots', 'POST', this.form)
        }
        this.reset()
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    edit(s) {
      this.editId = s.id
      this.form = { exam_id: s.exam_id, date: s.date, start_time: s.start_time, end_time: s.end_time, capacity: s.capacity }
      window.scrollTo(0, 0)
    },
    reset() {
      this.editId = null
      this.form = emptyForm()
    },
    async remove(s) {
      if (!confirm('Remove this slot?')) return
      this.error = ''
      try {
        await api('/examiner/slots/' + s.id, 'DELETE')
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    async showStudents(s) {
      this.viewing = s
      this.students = await api('/examiner/slots/' + s.id + '/students')
    },
  },
}
</script>
