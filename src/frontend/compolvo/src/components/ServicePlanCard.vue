<script lang="ts">
import {defineComponent, ref} from "vue"

interface SelectableAgent {
  props: {
    title: string
    subtitle: string
  }
  id: string
}

export default defineComponent({
  props: ["service_plan"],
  setup(props: { service_plan: ServicePlan }) {
    const plan = ref(props.service_plan)
    const cancelling = ref(false);
    const agents = ref<SelectableAgent[]>([]);
    const loadingAgents = ref(false);
    const selectedAgents = ref<SelectableAgent[]>([]);
    const installing = ref(false);
    const snackbarText = ref("");
    const showingSnackbar = ref(false);

    const cancel = async function () {
      cancelling.value = true;
      try {
        const res = await fetch("/api/service/plan/cancel?id=" + plan.value.id, {
          method: "DELETE"
        })
        if (!res.ok) {
          alert(await res.text());
        } else {
          await fetchData();
        }
      } catch (err) {
        alert(err)
      }
      cancelling.value = false;
    }

    const fetchData = async () => {
      try {
        const res = await fetch("/api/service/plan?id=" + plan.value.id)
        if (!res.ok) {
          alert(await res.text())
        } else {
          plan.value = JSON.parse(await res.text())[0];
        }
      } catch (err) {
        alert(err)
      }
    }

    const loadAgents = async function () {
      loadingAgents.value = true
      try {
        const res = await fetch("/api/agent?installable_for_service_plan=" + plan.value.id)
        if (!res.ok) {
          alert(await res.text())
        } else {
          agents.value = JSON.parse(await res.text())
            .map((agent: Agent) => {
              return {
                id: agent.id,
                props: {
                  title: agent.name || agent.id,
                  subtitle: (agent.connected ? "connected - " : "disconnected - ") + agent.id
                }
              }
            })
        }
      } catch (err) {
        alert(err)
      }
      loadingAgents.value = false
    }

    const install = async function (callback: () => void) {
      installing.value = true
      try {
        const res = await fetch("/api/agent/software/bulk", {
          method: "POST",
          body: JSON.stringify({
            service_plan: plan.value.id,
            agents: selectedAgents.value.map((agent) => agent.id)
          })
        })
        if (!res.ok) {
          alert(await res.text())
        } else {
          selectedAgents.value = []
          await callback()
        }
      } catch (err) {
        alert(err)
      }
      installing.value = false
    }

    return {
      plan,
      cancelling,
      agents,
      loadingAgents,
      selectedAgents,
      snackbarText,
      showingSnackbar,
      cancel,
      fetchData,
      install,
      loadAgents
    }
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
      <v-dialog
        v-if="plan.installable"
      >
        <template v-slot:activator="{ props: activatorProps}">
          <v-btn
            v-bind="activatorProps"
            @click="loadAgents"
            text="Install"
            prepend-icon="mdi-download"
            color="blue"
          ></v-btn>
        </template>
        <template v-slot:default="{ isActive }">
          <v-card class="pa-8">
            <h1>Install {{ plan.service_offering.service.name }}</h1>
            <v-progress-linear v-if="loadingAgents" indeterminate></v-progress-linear>
            Select agents to install {{ plan.service_offering.service.name }} on:
            <v-select
              v-if="agents.length > 0"
              v-model="selectedAgents"
              :items="agents"
              key="id"
              multiple
              clearable
              placeholder="Select agent"
              persistent-placeholder
            >
            </v-select>
            <div v-else>Create a new agent in the
              <RouterLink class="link" to="/agents">agent panel</RouterLink>
              first to select it here.
            </div>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                text="Install & close"
                @click="install(() => {
                    isActive.value = false
                    snackbarText = 'Software set up to be installed shortly.'
                    showingSnackbar = true
                    fetchData()
                  })"
              >
              </v-btn>
            </v-card-actions>
          </v-card>
        </template>
      </v-dialog>
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
    <v-snackbar color="success" v-model="showingSnackbar">
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn
          text="Close"
          variant="text"
          @click="showingSnackbar=false"
        >
        </v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<style scoped>

</style>
