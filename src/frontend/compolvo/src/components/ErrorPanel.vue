<script lang="ts">
import {defineComponent, ref} from "vue"

export default defineComponent({
  props: ["error"],
  setup(props: { error: Error | null }) {
    const error = ref(props.error)
    const errorText = ref(error.value?.message || "N/A")

    return {error, errorText}
  },
  watch: {
    error(value: Error | null): void {
      this.errorText.value = value?.message || "N/A"
    }
  }
})
</script>

<template>
  <div class="error-panel">
    <v-alert
      v-if="error != null"
      type="error"
      :text="errorText"
      closable
    ></v-alert>
  </div>
</template>

<style scoped>

</style>
