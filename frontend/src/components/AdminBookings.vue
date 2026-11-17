<template>
  <h3 class="mb-3">All Bookings (history)</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead><tr><th>Student</th><th>Examination</th><th>Date</th><th>Time</th><th>Examiner</th><th>Booked on</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="b in bookings" :key="b.id">
          <td>{{ b.student_name }}</td>
          <td>{{ b.exam_name }}</td>
          <td>{{ b.date }}</td>
          <td>{{ b.start_time }} - {{ b.end_time }}</td>
          <td>{{ b.examiner_name }}</td>
          <td>{{ b.booking_date }}</td>
          <td>{{ b.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary" v-if="b.status === 'Booked'" @click="start(b)">Reschedule</button>
          </td>
        </tr>
        <tr v-if="!bookings.length"><td colspan="8">No bookings</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card card-body" v-if="moving">
    <h5>Move {{ moving.student_name }} ({{ moving.exam_name }}) to another slot</h5>
    <form class="row g-2" @submit.prevent="save">
      <div class="col-md-8">
        <select class="form-select" v-model="newSlot" required>
          <option value="" disabled>Select slot</option>
          <option v-for="s in slots" :key="s.id" :value="s.id">
            {{ s.date }} {{ s.start_time }}-{{ s.end_time }} ({{ s.examiner_name }}, {{ s.available_seats }} seats left)
          </option>
        </select>
      </div>
      <div class="col-md-4">
        <button class="btn btn-primary">Move</button>
        <button type="button" class="btn btn-secondary ms-1" @click="moving = null">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { bookings: [], moving: null, slots: [], newSlot: '', error: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.bookings = await api('/admin/bookings')
    },
    async start(b) {
      this.moving = b
      this.newSlot = ''
      const all = await api('/admin/slots?exam_id=' + b.exam_id)
      // only other slots that still have seats
      this.slots = all.filter((s) => s.id !== b.slot_id && s.status === 'Available')
    },
    async save() {
      this.error = ''
      try {
        await api('/admin/bookings/' + this.moving.id + '/reschedule', 'PUT', { slot_id: this.newSlot })
        this.moving = null
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
