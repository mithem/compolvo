<template>
  <v-card class="pa-5">
    <v-card-title>Install agent</v-card-title>
    <ErrorPanel v-if="error !== null" :error="error"></ErrorPanel>
    <v-select
      label="Operating system"
      :items="oses"
      v-model="selectedOS"
    >
    </v-select>
    <v-select
      label="Architecture"
      :items="architectures"
      v-model="selectedArchitecture"
    >
    </v-select>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        prepend-icon="mdi-download"
        :disabled="selectedOS === null || selectedArchitecture === null"
        @click="downloadSelectedAgentDist"
      >Download
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, onMounted, ref} from "vue";
import {OperatingSystem} from "./models";

interface Architecture {
  title: string,
  id: string
}

export default defineComponent({
  data() {
    return {
      architectures: [
        {title: "x64", id: "x64"}
      ]
    }
  },
  setup() {
    const loading = ref(false)
    const error = ref<Error | null>(null)
    const oses = ref<OperatingSystem[]>([])
    const selectedOS = ref<OperatingSystem | null>(null)
    const selectedArchitecture = ref<Architecture | null>(null)
    const instance = getCurrentInstance()

    const fetchOperatingSystems = async () => {
      loading.value = true
      try {
        const res = await fetch("/api/operating-system")
        if (!res.ok) {
          error.value = Error(await res.text())
        } else {
          oses.value = (await res.json()).map(os => {
            return {
              ...os,
              props: {
                title: os.name
              }
            }
          })
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const downloadSelectedAgentDist = async () => {
      try {
        const filename = `compolvo-agent-${selectedOS.value.system_name}-${selectedArchitecture.value}`;
        const res = await fetch("/static/agent-dist/" + filename)
        if (!res.ok) {
          const errText = res.status === 404 ? "No agent installer found for this setup." : await res.text()
          error.value = Error(errText)
        } else {
          const url = window.URL.createObjectURL(await res.blob())
          const link = document.createElement("a")
          link.href = url
          link.setAttribute("download", filename)
          document.body.appendChild(link)
          link.click()
          window.URL.revokeObjectURL(url)
          link.remove()
          instance.proxy.$emit("close-card")
        }
      } catch (err) {
        error.value = err
      }
    }

    onMounted(fetchOperatingSystems)

    return {
      loading,
      error,
      oses,
      selectedOS,
      selectedArchitecture,
      fetchOperatingSystems,
      downloadSelectedAgentDist
    }
  }
})
</script>

<style scoped>

</style>
