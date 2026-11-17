<template>
  <h3 class="mb-3">Search</h3>
  <form class="row g-2 mb-3" @submit.prevent="search">
    <div class="col-md-3">
      <select class="form-select" v-model="type">
        <option value="students">Students</option>
        <option value="examiners">Examiners</option>
        <option value="exams">Examinations</option>
        <option value="bookings">Bookings</option>
      </select>
    </div>
    <div class="col-md-6">
      <input class="form-control" placeholder="Type a name, email, course..." v-model="q" />
    </div>
    <div class="col-md-3"><button class="btn btn-primary">Search</button></div>
  </form>

  <div class="table-responsive" v-if="searched">
    <table class="table table-bordered">
      <thead>
        <tr v-if="type === 'students' || type === 'examiners'"><th>Name</th><th>Username</th><th>Email</th><th>Department</th><th>Status</th></tr>
        <tr v-if="type === 'exams'"><th>Name</th><th>Course</th><th>Marks</th><th>Status</th></tr>
        <tr v-if="type === 'bookings'"><th>Student</th><th>Examination</th><th>Date</th><th>Examiner</th><th>Status</th></tr>
      </thead>
      <tbody>
        <template v-if="type === 'students' || type === 'examiners'">
          <tr v-for="r in results" :key="r.id">
            <td>{{ r.name }}</td><td>{{ r.username }}</td><td>{{ r.email }}</td><td>{{ r.department }}</td><td>{{ r.status }}</td>
          </tr>
        </template>
        <template v-if="type === 'exams'">
          <tr v-for="r in results" :key="r.id">
            <td>{{ r.name }}</td><td>{{ r.course_code }} - {{ r.course_name }}</td><td>{{ r.max_marks }}</td><td>{{ r.status }}</td>
          </tr>
        </template>
        <template v-if="type === 'bookings'">
          <tr v-for="r in results" :key="r.id">
            <td>{{ r.student_name }}</td><td>{{ r.exam_name }}</td><td>{{ r.date }}</td><td>{{ r.examiner_name }}</td><td>{{ r.status }}</td>
          </tr>
        </template>
        <tr v-if="!results.length"><td colspan="5">Nothing found</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { api } from '../api.js'

export default {
  data() {
    return { type: 'students', q: '', results: [], searched: false }
  },
  methods: {
    async search() {
      this.results = await api('/admin/search?type=' + this.type + '&q=' + encodeURIComponent(this.q))
      this.searched = true
    },
  },
}
</script>
