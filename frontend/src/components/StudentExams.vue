<template>
  <h3 class="mb-3">Examinations</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>
  <div class="alert alert-success" v-if="message">{{ message }}</div>

  <form class="row g-2 mb-3" @submit.prevent="load">
    <div class="col-md-4"><input class="form-control" placeholder="Search by name or course" v-model="q" /></div>
    <div class="col-md-3">
      <select class="form-select" v-model="courseId">
        <option value="">All courses</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} - {{ c.name }}</option>
      </select>
    </div>
    <div class="col-md-3">
      <select class="form-select" v-model="status">
        <option value="">All status</option>
        <option>Slot Creation</option>
        <option>Booking Open</option>
        <option>Closed</option>
        <option>Completed</option>
      </select>
    </div>
    <div class="col-md-2"><button class="btn btn-primary">Filter</button></div>
  </form>

  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead><tr><th>Examination</th><th>Course</th><th>Duration</th><th>Max marks</th><th>Booking period</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="e in exams" :key="e.id">
          <td>{{ e.name }}</td>
          <td>{{ e.course_code }} - {{ e.course_name }}</td>
          <td>{{ e.duration }} min</td>
          <td>{{ e.max_marks }}</td>
          <td>{{ e.booking_start }} to {{ e.booking_end }}</td>
          <td>{{ e.status }}</td>
          <td>
            <span v-if="e.my_booking_id" class="badge bg-success">Booked</span>
            <button v-else-if="e.status === 'Booking Open'" class="btn btn-sm btn-primary" @click="openSlots(e)">View slots</button>
          </td>
        </tr>
        <tr v-if="!exams.length"><td colspan="7">No examinations found</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card card-body" v-if="selected">
    <h5>Available slots for {{ selected.name }}</h5>
    <table class="table table-sm">
      <thead><tr><th>Date</th><th>Time</th><th>Examiner</th><th>Seats left</th><th></th></tr></thead>
      <tbody>
        <tr v-for="s in slots" :key="s.id">
          <td>{{ s.date }}</td>
          <td>{{ s.start_time }} - {{ s.end_time }}</td>
          <td>{{ s.examiner_name }}</td>
          <td>{{ s.available_seats }}</td>
          <td><button class="btn btn-sm btn-success" @click="book(s)">Book</button></td>
        </tr>
        <tr v-if="!slots.length"><td colspan="5">No slots available</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { exams: [], courses: [], q: '', courseId: '', status: '', selected: null, slots: [], error: '', message: '' }
  },
  async mounted() {
    this.courses = await api('/student/courses')
    this.load()
  },
  methods: {
    async load() {
      const params = '?q=' + encodeURIComponent(this.q) + '&course_id=' + this.courseId + '&status=' + encodeURIComponent(this.status)
      this.exams = await api('/student/exams' + params)
    },
    async openSlots(e) {
      this.selected = e
      this.slots = await api('/student/exams/' + e.id + '/slots')
    },
    async book(s) {
      this.error = ''
      this.message = ''
      try {
        const res = await api('/student/bookings', 'POST', { slot_id: s.id })
        this.message = res.message
        this.selected = null
        this.load()
      } catch (e) {
        this.error = e.message
        this.openSlots(this.selected)
      }
    },
  },
}
</script>
