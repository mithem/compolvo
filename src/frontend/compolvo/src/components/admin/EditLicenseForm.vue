<template>
  <v-form>
    <v-col>
      <v-text-field
        v-model="license.name"
        label="Name"
      ></v-text-field>
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
import {defineComponent, getCurrentInstance, ref} from 'vue';
import {UnsavedLicense} from "../models";

export default defineComponent({
  name: 'EditLicenseForm',
  props: ["license"],
  setup(props: {
    license: UnsavedLicense | null
  }) {
    const error = ref<Error | null>(null)
    const instance = getCurrentInstance()
    const license = ref<UnsavedLicense>({
      name: ""
    })
    if (props.license !== null) {
      license.value = props.license
    }

    const save = async function () {
      instance.proxy.$emit("license-save", license.value)
    }

    return {
      error,
      license,
      save
    }
  }
})
</script>

<style scoped>

</style>
