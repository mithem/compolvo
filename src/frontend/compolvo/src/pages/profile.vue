<script lang="ts">
import {defineComponent, onMounted, ref} from "vue";
import {ServicePlan} from "../components/models";


export default defineComponent({
  name: "Profile",
  setup() {
    const loading = ref(false);
    const deleting = ref(false);
    const svcPlans = ref<ServicePlan[]>([]);

    const fetchServicePlans = async function () {
      console.log("Fetching service plans")
      loading.value = true
      try {
        const res = await fetch("/api/service/plan")
        if (!res.ok) {
          alert(await res.text())
        } else {
          let text = await res.text();
          console.log(text)
          svcPlans.value = JSON.parse(text)
        }
      } catch (err) {
        alert(err)
      }
      loading.value = false
    }

    const deleteAccount = async function () {
      deleting.value = true
      const me = await fetch("/api/user/me")
      const id = (await me.json()).id
      const res = await fetch("/api/user?id=" + id, {
        method: "DELETE"
      })
      deleting.value = false
      if (res.ok) {
        document.location.pathname = "/"
      } else {
        alert(await res.text())
      }
    }

    onMounted(fetchServicePlans)

    return {loading, svcPlans, deleting, fetchServicePlans, deleteAccount}
  }
})
</script>

<template>
  <v-container fluid>
    <h1>Profile (+ Status)</h1>
    <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
    <v-container>
      <v-row>
        <v-col cols="12" md="6" lg="4" v-for="plan in svcPlans" :key="plan.id">
          <ServicePlanCard :service_plan="plan"></ServicePlanCard>
        </v-col>
      </v-row>
    </v-container>
    <v-btn
      @click="deleteAccount"
      :loading=deleting
      color="red"
    >Delete account
    </v-btn>
  </v-container>
</template>
