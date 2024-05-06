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
    const softwareCount = ref<number>(null);
    const me = ref<UserMeObject>(null);
    const loadingUserInfo = ref(false);
    const error = ref<Error | null>(null);

    const fetchServicePlans = async function () {
      loading.value = true
      try {
        const res = await fetch("/api/service/plan")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          let text = await res.text();
          svcPlans.value = JSON.parse(text)
          const activePlans = svcPlans.value.filter(plan => !plan.canceled_by_user)
          monthlyPrice.value = Math.round(activePlans.map((plan) => {
            return plan.service_offering.price / plan.service_offering.duration_days
          })
            .reduce((cost, newCost) => cost + newCost, 0) * 30 * 100) / 100
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const fetchUserInfo = async function () {
      loadingUserInfo.value = true
      const res = await fetch("/api/user/me")
      if (!res.ok) {
        error.value = new Error(await res.text())
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
        error.value = new Error(await res.text())
      }
    }

    const getAgentCount = async function () {
      try {
        const res = await fetch("/api/agent/count")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          const data = JSON.parse(await res.text())
          agentCount.value = data.count
        }
      } catch (err) {
        error.value = err
      }
    }

    const getSoftwareCount = async function () {
      try {
        const res = await fetch("/api/agent/software/count")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          const data = JSON.parse(await res.text())
          softwareCount.value = data.count
        }
      } catch (err) {
        error.value = err
      }
    }

    const loadStats = async function () {
      getAgentCount()
      getSoftwareCount()
    }

    onMounted(() => {
      fetchUserInfo()
      loadStats()
      fetchServicePlans()
    })

    return {
      loading,
      svcPlans,
      deleting,
      monthlyPrice,
      agentCount,
      softwareCount,
      me,
      loadingUserInfo,
      error,
      fetchServicePlans,
      deleteAccount,
      fetchUserInfo,
      loadStats
    }
  }
})
</script>

<template>
  <div class="profile-container">
    <h1>Profile</h1>
    <ErrorPanel v-if="error != null" :error=error/>
    <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
    <div class="stats-container">
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
      <v-card class="stat-card" title="Software count">
        <v-card-text class="stat-card-text">
          {{ softwareCount != null ? softwareCount : "N/A" }}
        </v-card-text>
      </v-card>
    </div>
    <div>
      <v-row>
        <v-col cols="12" md="6" lg="4" v-for="plan in svcPlans" :key="plan.id">
          <ServicePlanCard @reloadStats="loadStats();fetchServicePlans()"
                           :service_plan="plan"></ServicePlanCard>
        </v-col>
      </v-row>
    </div>
    <div class="form-container">
      <div v-if="me != null" class="user-form-container">
        <UserInfoForm :user=me></UserInfoForm>
      </div>
      <div v-else-if="loadingUserInfo">
        Loading user info...
        <v-progress-linear indeterminate></v-progress-linear>
      </div>
    </div>
    <v-btn
      @click="deleteAccount"
      :loading=deleting
      color="red"
    >Delete account
    </v-btn>
  </div>
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
  min-width: 150px;
}

.stat-card-text {
  font-size: 20px;
  font-weight: bold;
}

.profile-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin: 20px;
  width: 100%;
}

.form-container {
  display: flex;
  justify-content: center;
}

.user-form-container {
  width: 100%;
  max-width: 1000px;
}
</style>
