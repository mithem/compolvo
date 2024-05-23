<template>
  <ErrorPanel :error="error"></ErrorPanel>
  <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
  <v-form>
    <v-col>
      <v-row class="vert-input-field">
        <v-text-field
          class="horiz-input-field"
          v-model="svcSystemName"
          label="System name"
          mandatory
        ></v-text-field>
        <v-text-field
          class="horiz-input-field"
          v-model="svcName"
          label="Name"
          mandatory
        ></v-text-field>
      </v-row>
      <v-text-field
        v-model="svcShortDesc"
        label="Short description"
      ></v-text-field>
      <v-textarea
        v-model="svcDesc"
        label="Description"
      ></v-textarea>
      <v-text-field
        v-model="svcDownloadCount"
        label="Download count"
      ></v-text-field>
      <v-select
        v-model="selectedLicense"
        :items="licenses"
        label="License"
        mandatory
      >
      </v-select>
    </v-col>
  </v-form>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      text="Create"
      @click="createService"
    ></v-btn>
  </v-card-actions>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, Ref, ref} from 'vue';
import {License} from "../models";

export default defineComponent({
  name: 'NewServiceForm',
  props: ["licenses"],
  setup(props: {
    licenses: Ref<License[]>
  }) {
    const creating = ref(false)
    const error = ref<Error | null>(null)
    const svcName = ref("")
    const svcSystemName = ref("")
    const svcShortDesc = ref<string | null>(null)
    const svcDesc = ref("")
    const svcDownloadCount = ref(0)
    const selectedLicense = ref<License | null>(null)
    const licenses = props.licenses
    const instance = getCurrentInstance()

    const createService = async function () {
      creating.value = true
      const serviceData = {
        name: svcName.value,
        system_name: svcSystemName.value,
        short_description: svcShortDesc.value,
        description: svcDesc.value,
        download_count: Number(svcDownloadCount.value),
        license: selectedLicense.value.props.subtitle
      }
      const res = await fetch("/api/service", {
        method: "POST",
        body: JSON.stringify(serviceData)
      })
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        instance.proxy.$emit("service-created")
      }
      creating.value = false
    }


    return {
      error,
      svcName,
      svcSystemName,
      svcShortDesc,
      svcDesc,
      svcDownloadCount,
      creating,
      licenses,
      selectedLicense,
      createService
    }
  },
})
</script>

<style scoped>

</style>
