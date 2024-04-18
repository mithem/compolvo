<script lang="ts">
import {defineComponent, ref} from "vue"
import {ServicePlan} from "./models";

export default defineComponent({
  props: ["service_plan"],
  setup(props: { service_plan: ServicePlan }) {
    const plan = ref(props.service_plan)
    const cancelling = ref(false);

    const cancel = async function () {
      // TODO: Implement
      cancelling.value = true;
      try {
        const res = await fetch("/api/service/plan?id=" + plan.value.id, {
          method: "PATCH",
          body: JSON.stringify({
            canceled_by_user: true
          })
        })
        if (!res.ok) {
          alert(await res.text());
        } else {
          this.$emit("reload")
        }
      } catch (err) {
        alert(err)
      }
      cancelling.value = false;
    }

    return {plan, cancelling, cancel}
  }
})
</script>

<template>
  <v-card>
    <v-card-title>{{ plan.service_offering.service.name }}</v-card-title>
    <v-card-subtitle>{{ new Date(plan.start_date).toLocaleDateString() }}</v-card-subtitle>
    <v-card-text>
      {{ plan.service_offering.price }}€/{{ plan.service_offering.name }}
      <span v-if="plan.canceled_by_user" style="font-weight: bold"><br/>Canceled</span>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        @click="cancel()"
        :disabled="plan.canceled_by_user"
        :loading="cancelling"
        text="Cancel"
        variant="outlined"
        color="red"
      ></v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>

</style>
