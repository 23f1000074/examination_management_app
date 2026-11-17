<template>
  <h3 class="mb-3">Examinations</h3>
  <div class="alert alert-danger" v-if="error">{{ error }}</div>

  <!-- create / edit form -->
  <form class="card card-body mb-4" @submit.prevent="save">
    <h5>{{ editId ? 'Edit examination' : 'New examination' }}</h5>
    <div class="row g-2">
      <div class="col-md-4">
        <label class="form-label">Course</label>
        <select class="form-select" v-model="form.course_id" required>
          <option value="" disabled>Select course</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} - {{ c.name }}</option>
        </select>
      </div>
      <div class="col-md-4">
        <label class="form-label">Name</label>
        <input class="form-control" v-model="form.name" required />
      </div>
      <div class="col-md-4">
        <label class="form-label">Type</label>
        <select class="form-select" v-model="form.exam_type">
          <option>Examination</option>
          <option>Assessment</option>
        </select>
      </div>
      <div class="col-md-3">
        <label class="form-label">Duration (minutes)</label>
        <input type="number" min="1" class="form-control" v-model="form.duration" required />
      </div>
      <div class="col-md-3">
        <label class="form-label">Maximum marks</label>
        <input type="number" min="1" class="form-control" v-model="form.max_marks" required />
      </div>
      <div class="col-md-6">
        <label class="form-label">Instructions</label>
        <input class="form-control" v-model="form.instructions" />
      </div>
      <div class="col-md-3">
        <label class="form-label">Slot creation start</label>
        <input type="date" class="form-control" v-model="form.slot_create_start" required />
      </div>
      <div class="col-md-3">
        <label class="form-label">Slot creation end</label>
        <input type="date" class="form-control" v-model="form.slot_create_end" required />
      </div>
      <div class="col-md-3">
        <label class="form-label">Booking start</label>
        <input type="date" class="form-control" v-model="form.booking_start" required />
      </div>
      <div class="col-md-3">
        <label class="form-label">Booking end</label>
        <input type="date" class="form-control" v-model="form.booking_end" required />
      </div>
    </div>
    <div class="mt-3">
      <button class="btn btn-primary">{{ editId ? 'Update' : 'Create' }}</button>
      <button type="button" class="btn btn-secondary ms-2" v-if="editId" @click="reset">Cancel</button>
    </div>
  </form>

  <!-- list -->
  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead>
        <tr><th>Name</th><th>Course</th><th>Marks</th><th>Slot creation</th><th>Booking</th><th>Status</th><th>Examiners</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="e in exams" :key="e.id">
          <td>{{ e.name }}<br /><small class="text-muted">{{ e.exam_type }}, {{ e.duration }} min</small></td>
          <td>{{ e.course_code }}</td>
          <td>{{ e.max_marks }}</td>
          <td>{{ e.slot_create_start }}<br />to {{ e.slot_create_end }}</td>
          <td>{{ e.booking_start }}<br />to {{ e.booking_end }}</td>
          <td><span class="badge bg-secondary">{{ e.status }}</span></td>
          <td>
            <span v-for="x in e.examiners" :key="x.id" class="d-block">{{ x.name }}</span>
            <span v-if="!e.examiners.length">-</span>
          </td>
          <td>
            <div class="mb-1">
              <button class="btn btn-sm btn-outline-primary me-1" @click="edit(e)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="remove(e)">Delete</button>
            </div>
            <div class="mb-1">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openRubric(e)">Rubric</button>
              <button class="btn btn-sm btn-outline-secondary" @click="openAssign(e)">Examiners</button>
            </div>
            <div>
              <select class="form-select form-select-sm" :value="e.status" @change="setStatus(e, $event.target.value)">
                <option v-for="s in statuses" :key="s">{{ s }}</option>
              </select>
            </div>
          </td>
        </tr>
        <tr v-if="!exams.length"><td colspan="8">No examinations yet</td></tr>
      </tbody>
    </table>
  </div>
  <p class="text-muted">
    Use the status dropdown to control stages: "Slot Creation" opens slot creation for examiners,
    "Booking Open" opens booking for students, "Closed" closes booking.
  </p>

  <!-- rubric panel -->
  <div class="card card-body mb-3" v-if="rubricExam">
    <h5>Rubric for {{ rubricExam.name }} (max marks {{ rubricExam.max_marks }}, used {{ rubricTotal }})</h5>
    <form class="row g-2 mb-3" @submit.prevent="saveRubric">
      <div class="col-md-3"><input class="form-control" placeholder="Criterion" v-model="rform.criterion" required /></div>
      <div class="col-md-2"><input type="number" min="1" class="form-control" placeholder="Weightage" v-model="rform.weightage" required /></div>
      <div class="col-md-4"><input class="form-control" placeholder="Description" v-model="rform.description" /></div>
      <div class="col-md-3">
        <button class="btn btn-primary">{{ rEditId ? 'Update' : 'Add' }}</button>
        <button type="button" class="btn btn-secondary ms-1" @click="rubricExam = null">Close</button>
      </div>
    </form>
    <table class="table table-sm">
      <thead><tr><th>Criterion</th><th>Weightage</th><th>Description</th><th></th></tr></thead>
      <tbody>
        <tr v-for="r in rubrics" :key="r.id">
          <td>{{ r.criterion }}</td><td>{{ r.weightage }}</td><td>{{ r.description }}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary me-1" @click="editRubric(r)">Edit</button>
            <button class="btn btn-sm btn-outline-danger" @click="removeRubric(r)">Delete</button>
          </td>
        </tr>
        <tr v-if="!rubrics.length"><td colspan="4">No criteria yet</td></tr>
      </tbody>
    </table>
  </div>

  <!-- assign examiners panel -->
  <div class="card card-body mb-3" v-if="assignExam">
    <h5>Assign examiners to {{ assignExam.name }}</h5>
    <div class="form-check" v-for="x in examiners" :key="x.id">
      <input class="form-check-input" type="checkbox" :id="'ex' + x.id" :value="x.id" v-model="chosen" />
      <label class="form-check-label" :for="'ex' + x.id">{{ x.name }} ({{ x.department || 'no department' }})</label>
    </div>
    <div class="mt-2">
      <button class="btn btn-primary" @click="saveAssign">Save</button>
      <button class="btn btn-secondary ms-2" @click="assignExam = null">Close</button>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js'

const emptyForm = () => ({
  course_id: '', name: '', exam_type: 'Examination', duration: '', max_marks: '',
  instructions: '', slot_create_start: '', slot_create_end: '', booking_start: '', booking_end: '',
})

export default {
  data() {
    return {
      exams: [], courses: [], examiners: [],
      statuses: ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed'],
      form: emptyForm(), editId: null, error: '',
      rubricExam: null, rubrics: [], rform: { criterion: '', weightage: '', description: '' }, rEditId: null,
      assignExam: null, chosen: [],
    }
  },
  computed: {
    rubricTotal() {
      let total = 0
      for (const r of this.rubrics) total += r.weightage
      return total
    },
  },
  async mounted() {
    this.courses = await api('/admin/courses')
    this.examiners = await api('/admin/examiners')
    this.load()
  },
  methods: {
    async load() {
      this.exams = await api('/admin/exams')
    },
    async save() {
      this.error = ''
      try {
        if (this.editId) {
          await api('/admin/exams/' + this.editId, 'PUT', this.form)
        } else {
          await api('/admin/exams', 'POST', this.form)
        }
        this.reset()
        this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    edit(e) {
      this.editId = e.id
      this.form = {
        course_id: e.course_id, name: e.name, exam_type: e.exam_type, duration: e.duration,
        max_marks: e.max_marks, instructions: e.instructions,
        slot_create_start: e.slot_create_start, slot_create_end: e.slot_create_end,
        booking_start: e.booking_start, booking_end: e.booking_end,
      }
      window.scrollTo(0, 0)
    },
    reset() {
      this.editId = null
      this.form = emptyForm()
    },
    async remove(e) {
      if (!confirm('Delete ' + e.name + '?')) return
      this.error = ''
      try {
        await api('/admin/exams/' + e.id, 'DELETE')
        this.load()
      } catch (err) {
        this.error = err.message
      }
    },
    async setStatus(e, status) {
      this.error = ''
      try {
        await api('/admin/exams/' + e.id + '/status', 'PUT', { status: status })
      } catch (err) {
        this.error = err.message
      }
      this.load()
    },

    // rubric
    async openRubric(e) {
      this.rubricExam = e
      this.assignExam = null
      this.rEditId = null
      this.rform = { criterion: '', weightage: '', description: '' }
      this.rubrics = await api('/admin/exams/' + e.id + '/rubrics')
    },
    async saveRubric() {
      this.error = ''
      try {
        if (this.rEditId) {
          await api('/admin/rubrics/' + this.rEditId, 'PUT', this.rform)
        } else {
          await api('/admin/exams/' + this.rubricExam.id + '/rubrics', 'POST', this.rform)
        }
        this.openRubric(this.rubricExam)
      } catch (e) {
        this.error = e.message
      }
    },
    editRubric(r) {
      this.rEditId = r.id
      this.rform = { criterion: r.criterion, weightage: r.weightage, description: r.description }
    },
    async removeRubric(r) {
      await api('/admin/rubrics/' + r.id, 'DELETE')
      this.openRubric(this.rubricExam)
    },

    // examiners
    openAssign(e) {
      this.assignExam = e
      this.rubricExam = null
      this.chosen = e.examiners.map((x) => x.id)
    },
    async saveAssign() {
      await api('/admin/exams/' + this.assignExam.id + '/examiners', 'PUT', { examiner_ids: this.chosen })
      this.assignExam = null
      this.load()
    },
  },
}
</script>
