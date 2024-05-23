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
          <v-dialog max-width="750">
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
                  <NewServiceForm
                    @service-created="isActive.value = false;fetchServices()"
                    :licenses="licenses"
                  ></NewServiceForm>
                </v-col>
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
import {License, Service} from "../../components/models";

export default defineComponent({
  data() {
    return {
      singleSelect: false,
      headers: [
        {
          title: "ID",
          align: "start",
          key: "id"
        },
        {title: "System name", key: "system_name"},
        {title: "Short description", key: "short_description"},
        {title: "Description", key: "description"},
        {title: "Download count", key: "download_count"},
        {title: "Stripe product", key: "stripe_product_id"},
      ]
    }
  },
  setup() {
    const services = ref<Service[]>([])
    const selectedServices = ref<Service[]>([])
    const error = ref<Error | null>(null)
    const loading = ref(false)
    const deleting = ref(false)
    const licenses = ref<License[]>([])

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

    const deleteServices = async function () {
      deleting.value = true
      const res = await fetch("/api/service/bulk", {
        method: "DELETE",
        body: JSON.stringify({services: selectedServices.value})
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
        licenses.value = (await res.json()).map(license => {
          return {id: license.id, props: {title: license.name, subtitle: license.id}}
        })
      }
    }

    return {
      services,
      selectedServices,
      licenses,
      error,
      loading,
      deleting,
      fetchServices,
      deleteServices,
      fetchLicenses
    }
  },
  mounted() {
    this.fetchServices()
    this.fetchLicenses()
  }
})
</script>

<style scoped>

</style>
