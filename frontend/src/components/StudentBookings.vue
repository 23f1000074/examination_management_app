<template>
  <h3 class="mb-3">My Bookings and History</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>
  <div class="alert alert-success" v-if="message">{{ message }}</div>

  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead><tr><th>Examination</th><th>Course</th><th>Date</th><th>Time</th><th>Examiner</th><th>Booked on</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="b in bookings" :key="b.id">
          <td>{{ b.exam_name }}</td>
          <td>{{ b.course }}</td>
          <td>{{ b.date }}</td>
          <td>{{ b.start_time }} - {{ b.end_time }}</td>
          <td>{{ b.examiner_name }}</td>
          <td>{{ b.booking_date }}</td>
          <td>{{ b.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-danger" v-if="b.status === 'Booked'" @click="cancel(b)">Cancel</button>
          </td>
        </tr>
        <tr v-if="!bookings.length"><td colspan="8">You have no bookings yet</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { bookings: [], error: '', message: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.bookings = await api('/student/bookings')
    },
    async cancel(b) {
      if (!confirm('Cancel booking for ' + b.exam_name + '?')) return
      this.error = ''
      this.message = ''
      try {
        const res = await api('/student/bookings/' + b.id, 'DELETE')
        this.message = res.message
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
