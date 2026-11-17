<template>
  <h3 class="mb-3">Admin Dashboard</h3>
  <div class="row g-3 mb-4" v-if="stats">
    <div class="col-6 col-md-4" v-for="c in cards" :key="c.label">
      <div class="card text-center">
        <div class="card-body">
          <h2>{{ stats[c.key] }}</h2>
          <div>{{ c.label }}</div>
        </div>
      </div>
    </div>
  </div>

  <div class="row" v-if="stats">
    <div class="col-md-6">
      <h5>Popular examinations</h5>
      <table class="table table-sm">
        <thead><tr><th>Examination</th><th>Bookings</th></tr></thead>
        <tbody>
          <tr v-for="p in stats.popular_exams" :key="p.name"><td>{{ p.name }}</td><td>{{ p.count }}</td></tr>
          <tr v-if="!stats.popular_exams.length"><td colspan="2">No bookings yet</td></tr>
        </tbody>
      </table>
    </div>
    <div class="col-md-6">
      <h5>Examiner workload (slots)</h5>
      <table class="table table-sm">
        <thead><tr><th>Examiner</th><th>Slots</th></tr></thead>
        <tbody>
          <tr v-for="w in stats.examiner_workload" :key="w.name"><td>{{ w.name }}</td><td>{{ w.count }}</td></tr>
          <tr v-if="!stats.examiner_workload.length"><td colspan="2">No slots yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return {
      stats: null,
      cards: [
        { key: 'courses', label: 'Courses' },
        { key: 'exams', label: 'Examinations' },
        { key: 'students', label: 'Students' },
        { key: 'examiners', label: 'Examiners' },
        { key: 'bookings', label: 'Active bookings' },
        { key: 'completed', label: 'Completed evaluations' },
      ],
    }
  },
  async mounted() {
    this.stats = await api('/admin/stats')
  },
}
</script>
