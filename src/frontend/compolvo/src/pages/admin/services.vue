<template>
  <v-col>
    <ErrorPanel :error="error"></ErrorPanel>
    <v-data-table
      v-model="selectedServices"
      :headers="headers"
      :items="services"
      item-key="id"
      show-select
      class="elevation-1"
      :loading="loading"
    >
      <template v-slot:top>
        <v-toolbar title="Services">
          <v-btn
            @click="fetchServices"
            :loading="loading"
          >
            <template v-slot:prepend>
              <v-icon>mdi-refresh</v-icon>
            </template>
            Refresh
          </v-btn>
          <v-btn
            color="red"
            @click="deleteServices"
            :loading="deleting"
            :disabled="services.length === 0"
          >
            <template v-slot:prepend>
              <v-icon color="red">mdi-delete</v-icon>
            </template>
            Delete
          </v-btn>
          <v-dialog>
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn
                v-bind="activatorProps"
                color="blue"
              >
                <template v-slot:prepend>
                  <v-icon color="blue">mdi-plus</v-icon>
                </template>
                Create
              </v-btn>
            </template>
            <template v-slot:default="{ isActive }">
              <v-card class="pa-5">
                <v-col>
                  <h1>Create Service</h1>
                  <ErrorPanel :error="error"></ErrorPanel>
                  <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
                  <EditServiceForm
                    :service="null"
                    @service-save="createService($event).then(success => isActive.value = !success)"
                    :licenses="licenses"
                    :tags="tags"
                  ></EditServiceForm>
                </v-col>
              </v-card>
            </template>
          </v-dialog>
        </v-toolbar>
      </template>
      <template v-slot:item.actions="{item}">
        <v-dialog>
          <template v-slot:activator="{ props: activatorProps }">
            <v-btn v-bind="activatorProps" icon variant="text">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
          </template>
          <template v-slot:default="{ isActive }">
            <v-card class="pa-5">
              <v-col>
                <h1>Edit Service</h1>
                <div v-if="error !== null">
                  <ErrorPanel :error="error"></ErrorPanel>
                </div>
                <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
                <EditServiceForm
                  :service="item"
                  @service-save="editService(item.id, $event).then(success => isActive.value = !success)"
                  :licenses="licenses"
                  :tags="tags"
                ></EditServiceForm>
              </v-col>
            </v-card>
          </template>
        </v-dialog>
        <v-btn icon variant="text"
               @click="$router.push({path: `/admin/service/${item.id}/versions`})">
          <v-icon>mdi-cog</v-icon>
        </v-btn>
        <v-btn icon variant="text"
               @click="$router.push({path: `/admin/service/${item.id}/offerings`})">
          <v-icon>mdi-cash-multiple</v-icon>
        </v-btn>
      </template>
    </v-data-table>
  </v-col>
</template>

<script lang="ts">
import {defineComponent, ref} from "vue"
import {License, Service, Tag} from "../../components/models";
import {OptionalService} from "../../components/admin/EditServiceForm.vue";
import {removeKeysFromObject} from "../../components/utils"

export default defineComponent({
  data() {
    return {
      singleSelect: false,
      headers: [
        {title: "ID", key: "id"},
        {title: "System name", key: "system_name"},
        {title: "Name", key: "name"},
        {title: "Short description", key: "short_description"},
        {title: "Description", key: "description"},
        {title: "Download count", key: "download_count"},
        {title: "Actions", key: "actions"}
      ]
    }
  },
  setup() {
    const services = ref<Service[]>([])
    const selectedServices = ref<string[]>([])
    const error = ref<Error | null>(null)
    const loading = ref(false)
    const creating = ref(false)
    const deleting = ref(false)
    const licenses = ref<License[]>([])
    const tags = ref<Tag[]>([])

    const fetchServices = async function () {
      loading.value = true
      const res = await fetch("/api/service")
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        services.value = await res.json()
      }
      loading.value = false
    }

    const createService = async function (svc: OptionalService) {
      creating.value = true
      const res = await fetch("/api/service", {
        method: "POST",
        body: JSON.stringify(svc)
      })
      const success = res.ok;
      if (!success) {
        error.value = new Error(await res.text())
      } else {
        fetchServices()
      }
      creating.value = false
      return success
    }

    const deleteServices = async function () {
      deleting.value = true
      const res = await fetch("/api/service/bulk", {
        method: "DELETE",
        body: JSON.stringify({ids: selectedServices.value})
      })
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        await fetchServices()
      }
      deleting.value = false
    }

    const fetchLicenses = async function () {
      const res = await fetch("/api/license")
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        licenses.value = await res.json()
      }
    }

    const editService = async function (id: string, svc: OptionalService) {
      loading.value = true
      removeKeysFromObject(svc, ["id", "operating_systems", "offerings"]);
      const data = {...svc, tags: svc.tags.map(t => t.id)}
      const res = await fetch("/api/service?id=" + id, {
        method: "PATCH",
        body: JSON.stringify(data)
      })
      const success = res.ok;
      if (!success) {
        error.value = new Error(await res.text())
      } else {
        fetchServices()
      }
      loading.value = false
      return success
    }

    const fetchTags = async function () {
      const res = await fetch("/api/tag")
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        tags.value = await res.json()
      }
    }

    return {
      services,
      selectedServices,
      licenses,
      error,
      loading,
      creating,
      deleting,
      tags,
      fetchServices,
      createService,
      editService,
      deleteServices,
      fetchLicenses,
      fetchTags
    }
  },
  mounted() {
    this.fetchServices()
    this.fetchLicenses()
    this.fetchTags()
  }
})
</script>

<style scoped>

</style>
