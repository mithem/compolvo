<template>
  <v-container fluid>
    <v-container fluid class="container-row">
      <div>
        <ErrorPanel v-if="error != null" :error="error"/>
        <h2 @loggedIn="firstName = $event">Hello<span
          v-if="firstName !== null">, {{ firstName }}</span>!</h2>
        <div v-if="updates !== 0">There <span v-if="updates === 1">is</span><span
          v-else>are</span>
          {{ updates }} update<span v-if="updates > 1">s</span> available. Please apply any
          updates
          below.
        </div>
        <div v-else-if="softwares.length > 0">All agents up to date!</div>
        <div v-else>
          <span v-if="agentCount == 0">Add an agent in the
          <RouterLink class="link" to="/agents">agent panel</RouterLink>
          .<br/></span>
          <span v-else-if="servicePlanCount === 0">Check out new Software in the <RouterLink
            class="link"
            to="/compare">compare tab</RouterLink>.</span>
          <span v-else>You can install software on your agents from the
            <RouterLink class="link" to="/profile"
                        color="secondary">profile tab</RouterLink>.</span>
        </div>
        <br/>
        <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
      </div>
      <v-btn prepend-icon="mdi-refresh" @click="refresh">Refresh</v-btn>
    </v-container>
    <v-container>
      <v-row>
        <v-col cols="12" md="6" lg="4" v-for="software in softwares" :key="software.id">
          <AgentSoftwareCard :software="software" @reload="fetchSoftware"></AgentSoftwareCard>
        </v-col>
      </v-row>
    </v-container>
  </v-container>
</template>

<style scoped>
.container-row {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}
</style>

<script lang="ts">
import {defineComponent, onMounted, ref} from 'vue';
import AgentSoftwareCard from "../components/AgentSoftwareCard.vue";
import {AgentSoftware, UserMeObject} from "../components/models";
import {isHigherVersion} from "../components/utils";


export default defineComponent({
  components: {AgentSoftwareCard},
  setup() {
    const softwares = ref<AgentSoftware[]>([]);
    const updates = ref(0);
    const firstName = ref<string>(null);
    const loading = ref(false);
    const agentCount = ref<number>(null);
    const error = ref<Error | null>(null);
    const webSocket = new WebSocket("/api/notify");
    const servicePlanCount = ref<number>(null);


    const fetchSoftware = async function () {
      try {
        loading.value = true;
        const res = await fetch("/api/agent/software");
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          softwares.value = [];
          softwares.value = JSON.parse(await res.text())
          calculateAvailableUpdates()
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false;
    }

    const getServicePlanCount = async function () {
      const res = await fetch("/api/service/plan/count")
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        servicePlanCount.value = JSON.parse(await res.text()).count
      }
    }

    const calculateAvailableUpdates = function () {
      updates.value = softwares.value
        .filter(software => isHigherVersion(software.latest_version, software.installed_version))
        .length
    }

    const getUserName = async function () {
      try {
        const res = await fetch("/api/user/me")
        if (res.ok) {
          const user: UserMeObject = await res.json()
          firstName.value = user.first_name;
          subscribeToReloadEvents(user.id)
        }
      } catch (err) {
        error.value = err
      }
    }

    const subscribeToReloadEvents = async function (userId: string) {
      webSocket.send(JSON.stringify({
        intent: "subscribe",
        subscriber_type: "user",
        event_type: "reload",
        id: userId
      }))
    }

    const handleWebSocketMessage = async function (ev: MessageEvent) {
      const data = JSON.parse(ev.data)
      if (data.event && data.event.type === "reload" && data.event.message.path === "/home/agent/software") {
        fetchSoftware()
      } else {
        console.warn("Received invalid websocket message: ", ev.data)
      }
    }

    const getAgentCount = async function () {
      try {
        const res = await fetch("/api/agent/count")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          agentCount.value = JSON.parse(await res.text()).count
        }
      } catch (err) {
        error.value = err
      }
    }

    const refresh = async function () {
      await fetchSoftware()
      await getUserName()
      await getAgentCount()
      await getServicePlanCount()
    }

    onMounted(() => {
      refresh();
    });

    webSocket.onmessage = handleWebSocketMessage
    return {
      softwares,
      updates,
      firstName,
      loading,
      agentCount,
      servicePlanCount,
      error,
      fetchSoftware,
      refresh,
      getServicePlanCount
    }
  }
});
</script>
