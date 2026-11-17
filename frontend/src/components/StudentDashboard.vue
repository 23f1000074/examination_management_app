<template>
  <h3 class="mb-3">Student Dashboard</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>
  <div class="alert alert-info" v-if="info">{{ info }}</div>

  <div v-if="data">
    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card text-center"><div class="card-body"><h2>{{ data.available_exams.length }}</h2>Available examinations</div></div>
      </div>
      <div class="col-md-3">
        <div class="card text-center"><div class="card-body"><h2>{{ data.available_slots }}</h2>Available slots</div></div>
      </div>
      <div class="col-md-3">
        <div class="card text-center"><div class="card-body"><h2>{{ data.booked_slots.length }}</h2>Booked slots</div></div>
      </div>
      <div class="col-md-3">
        <div class="card text-center"><div class="card-body"><h2>{{ data.results.length }}</h2>Published results</div></div>
      </div>
    </div>

    <h5>Available examinations</h5>
    <ul>
      <li v-for="e in data.available_exams" :key="e.id">
        {{ e.name }} ({{ e.course_code }}) - booking till {{ e.booking_end }}
      </li>
      <li v-if="!data.available_exams.length">Nothing open for booking right now</li>
    </ul>

    <h5>Upcoming examinations (booking not open yet)</h5>
    <ul>
      <li v-for="e in data.upcoming_exams" :key="e.id">
        {{ e.name }} ({{ e.course_code }}) - booking starts {{ e.booking_start }}
      </li>
      <li v-if="!data.upcoming_exams.length">No upcoming examinations</li>
    </ul>

    <h5>My booked slots</h5>
    <ul>
      <li v-for="b in data.booked_slots" :key="b.id">
        {{ b.exam_name }} on {{ b.date }}, {{ b.start_time }} - {{ b.end_time }} ({{ b.examiner_name }})
      </li>
      <li v-if="!data.booked_slots.length">No booked slots</li>
    </ul>

    <h5>Published results</h5>
    <ul>
      <li v-for="r in data.results" :key="r.booking_id">{{ r.exam_name }}: {{ r.marks }} / {{ r.max_marks }}</li>
      <li v-if="!data.results.length">No results yet</li>
    </ul>

    <button class="btn btn-outline-primary" @click="exportCsv" :disabled="exporting">
      {{ exporting ? 'Exporting...' : 'Export my examination history (CSV)' }}
    </button>
  </div>
</template>

<script>
import { api, downloadFile } from '../api.js'

export default {
  data() {
    return { data: null, error: '', info: '', exporting: false }
  },
  async mounted() {
    this.data = await api('/student/dashboard')
  },
  methods: {
    // starts the celery job and then checks every 2 seconds until it is done
    async exportCsv() {
      this.error = ''
      this.info = ''
      this.exporting = true
      try {
        const job = await api('/student/export', 'POST')
        this.info = job.message
        const timer = setInterval(async () => {
          const s = await api('/student/export/' + job.task_id)
          if (s.state === 'done') {
            clearInterval(timer)
            this.exporting = false
            this.info = 'Export is ready, downloading...'
            await downloadFile('/student/export/file/' + s.file, s.file)
          } else if (s.state === 'failed') {
            clearInterval(timer)
            this.exporting = false
            this.error = 'Export failed'
          }
        }, 2000)
      } catch (e) {
        this.exporting = false
        this.error = e.message
      }
    },
  },
}
</script>
