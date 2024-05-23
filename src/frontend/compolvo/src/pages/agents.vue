<script lang="ts">
import {defineComponent, onMounted, ref} from "vue";
import {Agent} from "../components/models";


export default defineComponent({
  data() {
    return {
      singleSelect: false,
      selectedAgents: [],
      headers: [
        {
          title: "ID",
          align: "start",
          key: "id"
        },
        {title: "Name", key: "name"},
        {title: "Connected", key: "connected"},
        {title: "IP address", key: "connection_from_ip_address"},
        {title: "Last connection start", key: "last_connection_start"},
        {title: "Last connection end", key: "last_connection_end"},
        {title: "Connection interrupted", key: "connection_interrupted"},
        {title: "Initialized", key: "initialized"}
      ]
    }
  },
  setup() {
    const agents = ref<Agent[]>([]);
    const filteredAgents = ref<Agent[]>([]);
    const selectedAgents = ref<string[]>([]);
    const searchQuery = ref("");
    const loading = ref(false);
    const deleting = ref(false);
    const creating = ref(false);
    const newAgentID = ref<string>(null);
    const error = ref<Error | null>(null);
    const loadAgents = async function () {
      loading.value = true;
      try {
        const res = await fetch("/api/agent");
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          agents.value = JSON.parse(await res.text());
          await filterAgents();
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const filterAgents = async function () {
      console.log(filteredAgents)
      const searchKeys = ["id", "user", "name", "connected", "connection_from_ip_address", "last_connection_start", "last_connection_end", "connection_interrupted", "initialized"]
      const query = searchQuery.value.toLowerCase()
      filteredAgents.value = searchQuery.value == "" ? agents.value : agents.value.filter((agent: Agent) => {
        return searchKeys.some((key) => {
          const val = agent[key]
          return val !== null && val !== undefined && val.toString().toLowerCase().includes(query)
        })
      })
    }

    const deleteAgents = async function () {
      deleting.value = true;
      try {
        const res = await fetch("/api/agent/bulk", {
          method: "DELETE",
          body: JSON.stringify({
            ids: selectedAgents.value
          })
        });
        if (!res.ok) {
          error.value = new Error(await res.text());
        } else {
          await loadAgents();
        }
      } catch (err) {
        error.value = err
      }
      deleting.value = false;
    }

    const createAgent = async function () {
      creating.value = true;
      try {
        const res = await fetch("/api/agent", {
          method: "POST"
        })
        if (!res.ok) {
          error.value = new Error(await res.text());
        } else {
          const data = JSON.parse(await res.text())
          newAgentID.value = data.id
          await copyAgentID()
        }
      } catch (err) {
        error.value = err
      }
      creating.value = false;
    }

    const copyAgentID = async function () {
      await navigator.clipboard.writeText(newAgentID.value);
    }

    onMounted(loadAgents);
    return {
      agents,
      filteredAgents,
      selectedAgents,
      searchQuery,
      loading,
      deleting,
      creating,
      newAgentID,
      error,
      loadAgents,
      filterAgents,
      deleteAgents,
      createAgent,
      copyAgentID
    };
  },
  watch: {
    searchQuery(val) {
      this.filterAgents()
    },

  }
})
</script>

<template>
  <v-card class="agent-card">
    <ErrorPanel v-if="error != null" :error=error />
    <div v-if="this.agents.length === 0" class="mb-5">No agents. Add a new one in the toolbar.</div>
    <v-data-table
      v-model="selectedAgents"
      :headers="headers"
      :items="filteredAgents"
      item-key="id"
      show-select
      class="elevation-1"
      :loading="this.loading"
    >
      <template v-slot:top>
        <v-toolbar title="Agent management">
          <v-text-field
            prepend-icon="mdi-magnify"
            hide-details
            single-line
            v-model="searchQuery"
            placeholder="Search agents"
          ></v-text-field>
          <v-btn
            @click="loadAgents"
            :loading="loading"
          >
            <template v-slot:prepend>
              <v-icon>mdi-refresh</v-icon>
            </template>
            Refresh
          </v-btn>
          <v-btn
            color="red"
            @click="deleteAgents"
            :loading="deleting"
            :disabled="selectedAgents.length === 0"
          >
            <template v-slot:prepend>
              <v-icon color="red">mdi-delete</v-icon>
            </template>
            Delete
          </v-btn>
          <v-dialog max-width="750">
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn
                @click="createAgent"
                v-bind="activatorProps"
                color="blue"
              >
                <template v-slot:prepend>
                  <v-icon color="blue">mdi-plus</v-icon>
                </template>
                Create
              </v-btn>
            </template>
            <template v-slot:default="{ isActive }">
              <v-card class="pa-5">
                <v-col>
                  <h1>Create Agent</h1>
                  <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
                  <div>The new agent's ID is:
                    <v-skeleton-loader v-if="creating" type="text"></v-skeleton-loader>
                    <div v-else>{{ newAgentID }}
                    </div>
                  </div>
                  <span style="vertical-align: middle">
                    <v-icon color="green">mdi-check</v-icon>
                    copied to clipboard
                  </span>
                  <!--<br/><br/>
                  <div>Please run the following command on the machine you want to install the agent
                    on.
                  </div>-->
                  <!--TODO: Insert pagination for commands for different operating systems.-->
                  <v-card-actions>
                    <v-spacer/>
                    <v-btn
                      text="Done"
                      @click="isActive.value=false;loadAgents()"
                    ></v-btn>
                  </v-card-actions>
                </v-col>
              </v-card>
            </template>
          </v-dialog>
        </v-toolbar>
      </template>
    </v-data-table>
  </v-card>
</template>

<style scoped>
.agent-card {
  margin: 10px;
  padding: 7px;
  width: 100vw;
}
</style>
