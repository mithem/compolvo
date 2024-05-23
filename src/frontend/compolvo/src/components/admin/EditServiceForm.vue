<template>
  <v-form>
    <v-col>
      <v-row class="vert-input-field">
        <v-text-field
          class="horiz-input-field"
          v-model="service.system_name"
          label="System name"
          mandatory
        ></v-text-field>
        <v-text-field
          class="horiz-input-field"
          v-model="service.name"
          label="Name"
          mandatory
        ></v-text-field>
      </v-row>
      <v-text-field
        v-model="service.short_description"
        label="Short description"
      ></v-text-field>
      <v-textarea
        v-model="service.description"
        label="Description"
      ></v-textarea>
      <v-text-field
        v-model="service.download_count"
        label="Download count"
      ></v-text-field>
      <v-select
        v-model="service.license"
        :items="licenses"
        label="License"
        mandatory
      >
      </v-select>
      <v-row>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          text="Save"
          @click="save"
        ></v-btn>
      </v-row>
    </v-col>
  </v-form>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, Ref, ref} from 'vue';
import {License} from "../models";

export interface OptionalService {
  name: string,
  system_name: string,
  short_description: string | null,
  description: string | null,
  download_count: number,
  license: string | null
}

export default defineComponent({
  name: 'EditServiceForm',
  props: ["licenses", "service"],
  setup(props: {
    licenses: Ref<License[]>,
    service: OptionalService | null
  }) {
    const error = ref<Error | null>(null)
    const selectedLicense = ref<License | null>(null)
    const licenses = props.licenses
    const instance = getCurrentInstance()
    const service = ref<OptionalService>({
      name: "",
      system_name: "",
      short_description: "",
      description: "",
      download_count: 0,
      license: null
    })
    if (props.service !== null) {
      service.value = props.service
    }

    const save = async function () {
      service.value.license = service.value.license.id
      instance.proxy.$emit("service-save", service.value)
    }

    return {
      error,
      licenses,
      selectedLicense,
      service,
      save
    }
  },
})
</script>

<style scoped>

</style>
