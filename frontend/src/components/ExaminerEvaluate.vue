<template>
  <div v-if="data">
    <h3 class="mb-1">Evaluate {{ data.booking.student_name }}</h3>
    <p class="text-muted">{{ data.booking.exam_name }} | {{ data.booking.date }} {{ data.booking.start_time }}</p>

    <div class="alert alert-danger" v-if="error">{{ error }}</div>
    <div class="alert alert-success" v-if="message">{{ message }}</div>

    <p v-if="!data.rubrics.length" class="text-danger">The admin has not created a rubric for this examination yet.</p>

    <form @submit.prevent="submit" v-else>
      <table class="table table-bordered">
        <thead><tr><th>Criterion</th><th>Description</th><th>Max</th><th style="width:130px">Marks</th></tr></thead>
        <tbody>
          <tr v-for="r in data.rubrics" :key="r.id">
            <td>{{ r.criterion }}</td>
            <td>{{ r.description }}</td>
            <td>{{ r.weightage }}</td>
            <td><input type="number" min="0" :max="r.weightage" class="form-control" v-model="r.marks" required /></td>
          </tr>
          <tr>
            <th colspan="3" class="text-end">Total (out of {{ data.max_marks }})</th>
            <th>{{ total }}</th>
          </tr>
        </tbody>
      </table>
      <div class="mb-3">
        <label class="form-label">Remarks</label>
        <textarea class="form-control" rows="3" v-model="data.remarks" required></textarea>
      </div>
      <button class="btn btn-primary">Submit marks</button>
      <router-link to="/examiner/slots" class="btn btn-secondary ms-2">Back</router-link>
    </form>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { data: null, error: '', message: '' }
  },
  computed: {
    total() {
      let sum = 0
      for (const r of this.data.rubrics) sum += Number(r.marks) || 0
      return sum
    },
  },
  async mounted() {
    this.data = await api('/examiner/bookings/' + this.$route.params.id + '/evaluation')
  },
  methods: {
    async submit() {
      this.error = ''
      this.message = ''
      const scores = this.data.rubrics.map((r) => ({ rubric_id: r.id, marks: r.marks }))
      try {
        const res = await api('/examiner/bookings/' + this.$route.params.id + '/evaluate', 'POST',
          { scores: scores, remarks: this.data.remarks })
        this.message = res.message + ' (total ' + res.marks + ')'
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
