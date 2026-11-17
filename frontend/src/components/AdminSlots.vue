<template>
  <h3 class="mb-3">All Examiner Slots</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <div class="row mb-3">
    <div class="col-md-4">
      <select class="form-select" v-model="examFilter" @change="load">
        <option value="">All examinations</option>
        <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.name }}</option>
      </select>
    </div>
  </div>

  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead><tr><th>Examination</th><th>Examiner</th><th>Date</th><th>Time</th><th>Seats</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>
        <tr v-for="s in slots" :key="s.id">
          <td>{{ s.exam_name }}</td>
          <td>{{ s.examiner_name }}</td>
          <td>{{ s.date }}</td>
          <td>{{ s.start_time }} - {{ s.end_time }}</td>
          <td>{{ s.available_seats }} / {{ s.capacity }}</td>
          <td>{{ s.status }}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary me-1" @click="startReschedule(s)">Reschedule</button>
            <button class="btn btn-sm btn-outline-secondary" @click="startChange(s)">Change examiner</button>
          </td>
        </tr>
        <tr v-if="!slots.length"><td colspan="7">No slots</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card card-body mb-3" v-if="resched">
    <h5>Reschedule slot #{{ resched.id }}</h5>
    <form class="row g-2" @submit.prevent="saveResched">
      <div class="col-md-3"><input type="date" class="form-control" v-model="rform.date" required /></div>
      <div class="col-md-3"><input type="time" class="form-control" v-model="rform.start_time" required /></div>
      <div class="col-md-3"><input type="time" class="form-control" v-model="rform.end_time" required /></div>
      <div class="col-md-3">
        <button class="btn btn-primary">Save</button>
        <button type="button" class="btn btn-secondary ms-1" @click="resched = null">Cancel</button>
      </div>
    </form>
  </div>

  <div class="card card-body mb-3" v-if="changing">
    <h5>Change examiner for slot #{{ changing.id }}</h5>
    <form class="row g-2" @submit.prevent="saveChange">
      <div class="col-md-6">
        <select class="form-select" v-model="newExaminer" required>
          <option value="" disabled>Select examiner</option>
          <option v-for="x in examiners" :key="x.id" :value="x.id">{{ x.name }}</option>
        </select>
      </div>
      <div class="col-md-6">
        <button class="btn btn-primary">Save</button>
        <button type="button" class="btn btn-secondary ms-1" @click="changing = null">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return {
      slots: [], exams: [], examiners: [], examFilter: '', error: '',
      resched: null, rform: {}, changing: null, newExaminer: '',
    }
  },
  async mounted() {
    this.exams = await api('/admin/exams')
    this.examiners = (await api('/admin/examiners')).filter((x) => x.status === 'Active')
    this.load()
  },
  methods: {
    async load() {
      const q = this.examFilter ? '?exam_id=' + this.examFilter : ''
      this.slots = await api('/admin/slots' + q)
    },
    startReschedule(s) {
      this.changing = null
      this.resched = s
      this.rform = { date: s.date, start_time: s.start_time, end_time: s.end_time }
    },
    async saveResched() {
      this.error = ''
      try {
        await api('/admin/slots/' + this.resched.id, 'PUT', this.rform)
        this.resched = null
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    startChange(s) {
      this.resched = null
      this.changing = s
      this.newExaminer = ''
    },
    async saveChange() {
      this.error = ''
      try {
        await api('/admin/slots/' + this.changing.id + '/examiner', 'PUT', { examiner_id: this.newExaminer })
        this.changing = null
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
  },
}
</script>
