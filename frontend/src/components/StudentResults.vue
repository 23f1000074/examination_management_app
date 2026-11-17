<template>
  <h3 class="mb-3">Published Results</h3>
  <div class="card mb-3" v-for="r in results" :key="r.booking_id">
    <div class="card-body">
      <h5>{{ r.exam_name }} <small class="text-muted">({{ r.course }})</small></h5>
      <p class="mb-1">Date: {{ r.date }} | Examiner: {{ r.examiner_name }}</p>
      <p class="mb-2"><b>Marks: {{ r.marks }} / {{ r.max_marks }}</b></p>
      <table class="table table-sm w-auto">
        <thead><tr><th>Criterion</th><th>Marks</th></tr></thead>
        <tbody>
          <tr v-for="s in r.scores" :key="s.criterion"><td>{{ s.criterion }}</td><td>{{ s.marks }} / {{ s.max }}</td></tr>
        </tbody>
      </table>
      <p class="mb-0"><b>Examiner feedback:</b> {{ r.remarks }}</p>
    </div>
  </div>
  <p v-if="!results.length">No results have been published yet.</p>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { results: [] }
  },
  async mounted() {
    this.results = await api('/student/results')
  },
}
</script>
