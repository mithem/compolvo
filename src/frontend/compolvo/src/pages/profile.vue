<script lang="ts">
import {defineComponent, onMounted, ref} from "vue";
import {ServicePlan, UserMeObject} from "../components/models";


export default defineComponent({
  name: "Profile",
  setup() {
    const loading = ref(false);
    const deleting = ref(false);
    const svcPlans = ref<ServicePlan[]>([]);
    const monthlyPrice = ref<number>(null);
    const agentCount = ref<number>(null);
    const me = ref<UserMeObject>(null);
    const loadingUserInfo = ref(false);

    const fetchServicePlans = async function () {
      loading.value = true
      try {
        const res = await fetch("/api/service/plan")
        if (!res.ok) {
          alert(await res.text())
        } else {
          let text = await res.text();
          console.log(text)
          svcPlans.value = JSON.parse(text)
          monthlyPrice.value = Math.round(svcPlans.value.map((plan) => {
            return plan.service_offering.price / plan.service_offering.duration_days
          })
            .reduce((cost, newCost) => cost + newCost, 0) * 30 * 100) / 100
        }
      } catch (err) {
        alert(err)
      }
      loading.value = false
    }

    const fetchUserInfo = async function () {
      loadingUserInfo.value = true
      const res = await fetch("/api/user/me")
      if (!res.ok) {
        alert(await res.text())
      } else {
        me.value = await res.json()
      }
      loadingUserInfo.value = false
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

    const getAgentCount = async function () {
      try {
        const res = await fetch("/api/agent/count")
        if (!res.ok) {
          alert(await res.text())
        } else {
          const data = JSON.parse(await res.text())
          agentCount.value = data.count
        }
      } catch (err) {
        alert(err)
      }
    }

    onMounted(() => {
      fetchUserInfo()
      getAgentCount()
      fetchServicePlans()
    })

    return {
      loading,
      svcPlans,
      deleting,
      monthlyPrice,
      agentCount,
      me,
      loadingUserInfo,
      fetchServicePlans,
      deleteAccount,
      fetchUserInfo
    }
  }
})
</script>

<template>
  <v-container fluid>
    <h1>Profile (+ Status)</h1>
    <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
    <v-container class="stats-container">
      <v-card class="stat-card" title="Total service plans">
        <v-card-text class="stat-card-text">{{ svcPlans.length }}</v-card-text>
      </v-card>
      <v-card class="stat-card" title="Total cost">
        <v-card-text class="stat-card-text">{{ monthlyPrice }}€/month
        </v-card-text>
      </v-card>
      <v-card class="stat-card" title="Agent count">
        <v-card-text class="stat-card-text">{{
            agentCount != null ? agentCount : "N/A"
          }}
        </v-card-text>
      </v-card>
    </v-container>
    <v-container>
      <v-row>
        <v-col cols="12" md="6" lg="4" v-for="plan in svcPlans" :key="plan.id">
          <ServicePlanCard :service_plan="plan"></ServicePlanCard>
        </v-col>
      </v-row>
    </v-container>
    <div v-if="me != null">
      <UserInfoForm :user=me></UserInfoForm>
    </div>
    <div v-else-if="loadingUserInfo">
      Loading user info...
      <v-progress-linear indeterminate></v-progress-linear>
    </div>
    <v-btn
      @click="deleteAccount"
      :loading=deleting
      color="red"
    >Delete account
    </v-btn>
  </v-container>
</template>

<style scoped>
.stats-container {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.stat-card {
  flex-basis: 100%;
  border-radius: 10px;
}

.stat-card-text {
  font-size: 20px;
  font-weight: bold;
}
</style>
