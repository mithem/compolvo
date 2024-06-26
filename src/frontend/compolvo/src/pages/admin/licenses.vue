<template>
  <v-col>
    <div v-if="error !== null">
      <ErrorPanel :error="error"></ErrorPanel>
    </div>
    <v-data-table
      v-model="selectedLicenses"
      :headers="headers"
      :items="licenses"
      item-key="id"
      show-select
      class="elevation-1"
      :loading="loading"
    >
      <template v-slot:top>
        <v-toolbar title="Licenses">
          <v-btn prepend-icon="mdi-refresh" @click="fetchLicenses">Refresh</v-btn>
          <v-btn prepend-icon="mdi-delete" color="red" @click="deleteLicenses">Delete</v-btn>
          <v-dialog>
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" color="blue">
                <v-icon color="blue">mdi-plus</v-icon>
                Create
              </v-btn>
            </template>
            <template v-slot:default="{isActive}">
              <v-card class="pa-5">
                <v-card-title>Create license</v-card-title>
                <EditLicenseForm
                  :license="null"
                  @license-save="createLicense($event).then(success => {if (success) isActive.value = false})"
                ></EditLicenseForm>
              </v-card>
            </template>
          </v-dialog>
        </v-toolbar>
      </template>
    </v-data-table>
  </v-col>
</template>

<script lang="ts">
import {defineComponent, ref} from "vue"
import {License, UnsavedLicense} from "../../components/models";
import EditLicenseForm from "../../components/admin/EditLicenseForm.vue";

export default defineComponent({
  components: {EditLicenseForm},
  data() {
    return {
      singleSelect: false,
      headers: [
        {title: "ID", key: "id"},
        {title: "Name", key: "name"},
      ]
    }
  },
  setup() {
    const loading = ref(false)
    const creating = ref(false)
    const deleting = ref(false)
    const error = ref<Error | null>(null)
    const licenses = ref<License[]>([])
    const selectedLicenses = ref<string[]>([])

    const fetchLicenses = async () => {
      loading.value = true
      try {
        const res = await fetch("/api/license")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          licenses.value = await res.json()
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const deleteLicenses = async () => {
      deleting.value = true
      try {
        const res = await fetch("/api/license/bulk", {
          method: "DELETE",
          body: JSON.stringify({ids: selectedLicenses.value})
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          selectedLicenses.value = []
          fetchLicenses()
        }
      } catch (err) {
        error.value = err
      }
      deleting.value = false
    }

    const createLicense = async (license: UnsavedLicense) => {
      creating.value = true
      const res = await fetch("/api/license", {
        method: "POST",
        body: JSON.stringify(license)
      })
      const success = res.ok;
      if (!success) {
        error.value = new Error(await res.text())
      } else {
        fetchLicenses()
      }
      creating.value = false
      return success
    }

    return {
      loading,
      creating,
      licenses,
      selectedLicenses,
      error,
      fetchLicenses,
      createLicense,
      deleteLicenses
    }
  },
  mounted() {
    this.fetchLicenses()
  }
})
</script>

<style scoped>

</style>
