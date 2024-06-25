<template>
  <v-form>
    <v-col>
      <v-text-field
        v-model="tag.label"
        label="Label"
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
import {UnsavedTag} from "../models";

export default defineComponent({
  name: 'EditTagForm',
  props: ["tag"],
  setup(props: {
    tag: UnsavedTag | null
  }) {
    const error = ref<Error | null>(null)
    const instance = getCurrentInstance()
    const tag = ref<UnsavedTag>({
      label: ""
    })
    if (props.tag !== null) {
      tag.value = props.tag
    }

    const save = async function () {
      instance.proxy.$emit("tag-save", tag.value)
    }

    return {
      error,
      tag,
      save
    }
  },
})
</script>

<style scoped>

</style>
