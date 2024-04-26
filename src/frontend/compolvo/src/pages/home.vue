<template>
  <v-container fluid>
    <v-container fluid style="display: flex">
      <v-container>
        <h2 @loggedIn="firstName = $event">Hello<span
          v-if="firstName !== null">, {{ firstName }}</span>!</h2>
        <div v-if="updates !== 0">There <span v-if="updates === 1">is</span><span v-else>are</span>
          {{ updates }} update<span v-if="updates > 1">s</span> available. Please apply any updates
          below.
        </div>
        <div v-else-if="softwares.length > 0">All agents up to date!</div>
        <div v-else>
          <span v-if="agentCount == 0">Add an agent in the
          <RouterLink class="link" to="/agents">agent panel</RouterLink>
          .<br/></span>
          <span v-else>You can install software on your agents from the
            <RouterLink class="link" to="/profile">profile tab</RouterLink>.</span>
          Or check out new Software in the
          <RouterLink class="link" to="/compare">compare tab</RouterLink>
          .
        </div>
        <br/>
        <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
      </v-container>
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

<script lang="ts">
import {defineComponent, onMounted, ref} from 'vue';
import AgentSoftwareCard from "../components/AgentSoftwareCard.vue";
import {AgentSoftware, User} from "../components/models";
import {isHigherVersion} from "../components/utils";


export default defineComponent({
  components: {AgentSoftwareCard},
  setup() {
    const softwares = ref<AgentSoftware[]>([]);
    const updates = ref(0);
    const firstName = ref<string>(null);
    const loading = ref(false);
    const agentCount = ref<number>(null)
    const fetchSoftware = async function () {
      try {
        loading.value = true;
        const res = await fetch("/api/agent/software");
        if (!res.ok) {
          alert(await res.text());
        } else {
          softwares.value = []
          softwares.value = JSON.parse(await res.text())
          calculateAvailableUpdates()
        }
      } catch (err) {
        alert(err)
      }
      loading.value = false;
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
          const user: User = JSON.parse(await res.text());
          firstName.value = user.first_name;
        }
      } catch (err) {
      }
    }

    const getAgentCount = async function () {
      try {
        const res = await fetch("/api/agent/count")
        if (!res.ok) {
          alert(await res.text())
        } else {
          agentCount.value = JSON.parse(await res.text()).count
        }
      } catch (err) {
        alert(err)
      }
    }

    const refresh = async function () {
      await fetchSoftware()
      await getUserName()
      await getAgentCount()
    }

    onMounted(() => {
      refresh();
    });

    return {softwares, updates, firstName, loading, agentCount, fetchSoftware, refresh}
  }
});
</script>
