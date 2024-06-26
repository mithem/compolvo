<template>
  <v-form>
    <v-col>
      <v-row class="horiz-input-field">
        <v-switch
          inline
          v-model="offering.active"
          class="vert-input-field"
          label="Active"
        ></v-switch>
        <v-text-field
          v-model="offering.name"
          class="vert-input-field"
          label="Name"
        ></v-text-field>
      </v-row>
      <v-text-field
        v-model="offering.description"
        label="Description"
      ></v-text-field>
      <v-text-field
        v-model="offering.price"
        label="Price"
        min="0"
        step="0.01"
      ></v-text-field>
      <v-text-field
        v-model="offering.duration_days"
        label="Duration (days)"
        min="1"
        max="1095"
        step="1"
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
import {ServiceOffering} from "../models";
import {OptionalServiceOffering} from "../utils";

export default defineComponent({
  name: 'EditServiceOfferingForm',
  props: ["offering"],
  setup(props: {
    offering: ServiceOffering | null
  }) {
    const error = ref<Error | null>(null)
    const instance = getCurrentInstance()
    const offering = ref<OptionalServiceOffering>({
      id: undefined,
      name: "",
      description: "",
      price: 0.00,
      duration_days: 30,
      service: ""
    })
    if (props.offering !== null) {
      offering.value = props.offering
    }

    const save = async function () {
      instance.proxy.$emit("offering-save", offering.value)
    }

    return {
      error,
      offering,
      save
    }
  }
})
</script>

<style scoped>

</style>
