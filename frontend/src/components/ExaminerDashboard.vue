<template>
  <h3 class="mb-3">Examiner Dashboard</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <div class="row g-3 mb-4" v-if="data">
    <div class="col-md-4">
      <div class="card text-center"><div class="card-body"><h2>{{ data.slot_count }}</h2>Slots created</div></div>
    </div>
    <div class="col-md-4">
      <div class="card text-center"><div class="card-body"><h2>{{ data.booked_students }}</h2>Booked students</div></div>
    </div>
    <div class="col-md-4">
      <div class="card text-center"><div class="card-body"><h2>{{ data.pending_evaluations }}</h2>Pending evaluations</div></div>
    </div>
  </div>

  <h5>Assigned examinations</h5>
  <div class="table-responsive" v-if="data">
    <table class="table table-bordered">
      <thead><tr><th>Examination</th><th>Course</th><th>Slot creation</th><th>Booking</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="e in data.exams" :key="e.id">
          <td>{{ e.name }}</td>
          <td>{{ e.course_code }}</td>
          <td>{{ e.slot_create_start }} to {{ e.slot_create_end }}</td>
          <td>{{ e.booking_start }} to {{ e.booking_end }}</td>
          <td>{{ e.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-secondary me-1" v-if="e.status === 'Booking Open'" @click="setStatus(e, 'Closed')">Close booking</button>
            <button class="btn btn-sm btn-outline-success" v-if="e.status === 'Booking Open' || e.status === 'Closed'" @click="setStatus(e, 'Completed')">Mark completed</button>
          </td>
        </tr>
        <tr v-if="!data.exams.length"><td colspan="6">No examinations assigned to you yet</td></tr>
      </tbody>
    </table>
  </div>
  <router-link to="/examiner/slots" class="btn btn-primary">Manage my slots</router-link>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { data: null, error: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.data = await api('/examiner/dashboard')
    },
    async setStatus(e, status) {
      this.error = ''
      try {
        await api('/examiner/exams/' + e.id + '/status', 'PUT', { status: status })
        this.load()
      } catch (err) {
        this.error = err.message
      }
    },
  },
}
</script>
