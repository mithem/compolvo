<template>
  <v-col>
    <h2>Service offerings</h2>
    <h3 style="color: rgb(var(--v-theme-text-secondary))">{{ serviceName }}</h3>
    <div v-if="error !== null">
      <ErrorPanel :error="error"></ErrorPanel>
    </div>
    <v-data-table
      v-model="selectedOfferings"
      :headers="headers"
      :items="offerings"
      item-key="id"
      show-select
      class="elevation-1"
      :loading="loading"
    >
      <template v-slot:top>
        <v-toolbar title="Offerings">
          <v-btn
            prepend-icon="mdi-refresh"
            :loading="loading"
            @click="fetchOfferings"
          >Reload
          </v-btn>
          <v-btn
            color="red"
            prepend-icon="mdi-delete"
            :loading="deleting"
            :disabled="selectedOfferings.length === 0"
            @click="deleteOfferings"
          >Delete
          </v-btn>
          <v-dialog>
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" prepend-icon="mdi-plus" variant="text" color="blue">
                Create
              </v-btn>
            </template>
            <template v-slot:default="{ isActive }">
              <v-card class="pa-5">
                <v-col>
                  <v-card-title>Create Offering</v-card-title>
                  <div v-if="error !== null">
                    <ErrorPanel :error="error"></ErrorPanel>
                  </div>
                  <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
                  <EditServiceOfferingForm
                    :offering="null"
                    @offering-save="createOffering($event).then(success => isActive.value = !success)"
                  ></EditServiceOfferingForm>
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
                <v-card-title>Edit Offering</v-card-title>
                <div v-if="error !== null">
                  <ErrorPanel :error="error"></ErrorPanel>
                </div>
                <v-progress-linear v-if="loading" indeterminate :height="5"></v-progress-linear>
                <EditServiceOfferingForm
                  :offering="item"
                  @offering-save="editOffering($event).then(success => isActive.value = !success)"
                ></EditServiceOfferingForm>
              </v-col>
            </v-card>
          </template>
        </v-dialog>
      </template>
    </v-data-table>
  </v-col>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, ref} from 'vue';
import {ServiceOffering} from "../../../../components/models";
import {OptionalServiceOffering, removeKeysFromObject} from "../../../../components/utils";

export default defineComponent({
  data() {
    return {
      headers: [
        {title: "Name", key: "name"},
        {title: "Description", key: "description"},
        {title: "Price", key: "price"},
        {title: "Duration (days)", key: "duration_days"},
        {title: "Actions", key: "actions"}
      ]
    }
  },
  setup() {
    const loading = ref(false)
    const creating = ref(false)
    const deleting = ref(false)
    const error = ref<Error | null>(null)
    const offerings = ref<ServiceOffering[]>([])
    const selectedOfferings = ref<ServiceOffering[]>([])
    const serviceName = ref("")
    const instance = getCurrentInstance()

    const fetchOfferings = async function () {
      loading.value = true
      try {
        const res = await fetch("/api/service/offering?service=" + instance.proxy.$route.params.id)
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          offerings.value = await res.json()
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const fetchServiceName = async function () {
      const res = await fetch("/api/service?id=" + instance.proxy.$route.params.id)
      if (res.ok) {
        serviceName.value = (await res.json()).name
      } else {
        serviceName.value = ""
      }
    }

    const createOffering = async function (offering: OptionalServiceOffering) {
      creating.value = true
      offering.service = instance.proxy.$route.params.id.toString()
      const res = await fetch("/api/service/offering", {
        method: "POST",
        body: JSON.stringify(offering)
      })
      const success = res.ok;
      if (!success) {
        error.value = new Error(await res.text())
      } else {
        fetchOfferings()
      }
      creating.value = false
      return success
    }

    const deleteOfferings = async function () {
      deleting.value = true
      try {
        const res = await fetch("/api/service/offering/bulk", {
          method: "DELETE",
          body: JSON.stringify({ids: selectedOfferings.value})
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          fetchOfferings()
        }
      } catch (err) {
        error.value = err
      }
      deleting.value = false
    }

    const editOffering = async function (offering: ServiceOffering) {
      loading.value = true
      const id = offering.id
      removeKeysFromObject(offering, ["id"])
      const res = await fetch("/api/service/offering?id=" + id, {
        method: "PATCH",
        body: JSON.stringify(offering)
      })
      const success = res.ok;
      if (!success) {
        error.value = new Error(await res.text())
      } else {
        fetchOfferings()
      }
      loading.value = false
      return success
    }

    return {
      loading,
      creating,
      deleting,
      error,
      offerings,
      selectedOfferings,
      serviceName,
      fetchOfferings,
      createOffering,
      editOffering,
      deleteOfferings,
      fetchServiceName
    };
  },
  mounted() {
    this.fetchOfferings()
    this.fetchServiceName()
  }
})
</script>

<style scoped>

</style>
