<template>
  <v-col>
    <h2>Service versions</h2>
    <h3 style="color: rgb(var(--v-theme-text-secondary))">{{ serviceName }}</h3>
    <div v-if="error !== null">
      <ErrorPanel :error="error"></ErrorPanel>
    </div>
    <v-data-table
      v-model="selectedVersions"
      :headers="headers"
      :items="versions"
      item-key="id"
      show-select
      class="elevation-1"
      :loading="loading"
    >
      <template v-slot:top>
        <v-toolbar title="Versions">
          <v-btn
            prepend-icon="mdi-refresh"
            :loading="loading"
            @click="fetchPackageManagerAvailableVersions"
          >Reload
          </v-btn>
          <v-btn
            color="red"
            prepend-icon="mdi-delete"
            :loading="deleting"
            :disabled="selectedVersions.length === 0"
            @click="deleteVersions"
          >Delete
          </v-btn>
        </v-toolbar>
      </template>
    </v-data-table>
  </v-col>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, ref} from 'vue';
import {PackageManagerAvailableVersion} from "../../../../components/models";

export default defineComponent({
  data() {
    return {
      headers: [
        {title: "Version", key: "version"},
        {title: "Latest", key: "latest"},
        {title: "OS", key: "os"},
        {title: "Package manager", key: "pm"}
      ]
    }
  },
  setup() {
    const loading = ref(false)
    const deleting = ref(false)
    const error = ref<Error | null>(null)
    const versions = ref<PackageManagerAvailableVersion[]>([])
    const selectedVersions = ref<PackageManagerAvailableVersion[]>([])
    const serviceName = ref("")
    const instance = getCurrentInstance()

    const fetchPackageManagerAvailableVersions = async function () {
      loading.value = true
      try {
        const res = await fetch("/api/service/version?service_id=" + instance.proxy.$route.params.id)
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          versions.value = (await res.json()).map(version => {
            return {
              ...version,
              os: version.operating_system.name,
              pm: version.package_manager.name
            }
          })
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

    const deleteVersions = async function () {
      deleting.value = true
      try {
        const res = await fetch("/api/service/version/bulk", {
          method: "DELETE",
          body: JSON.stringify({ids: selectedVersions.value})
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          fetchPackageManagerAvailableVersions()
        }
      } catch (err) {
        error.value = err
      }
      deleting.value = false
    }

    return {
      loading,
      deleting,
      error,
      versions,
      selectedVersions,
      serviceName,
      fetchPackageManagerAvailableVersions,
      deleteVersions,
      fetchServiceName
    };
  },
  mounted() {
    this.fetchPackageManagerAvailableVersions()
    this.fetchServiceName()
  }
})
</script>

<style scoped>

</style>
