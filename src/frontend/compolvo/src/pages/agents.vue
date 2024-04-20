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
        {title: "User", key: "user"},
        {title: "Last connection start", key: "lastConnectionStart"},
        {title: "Last connection end", key: "lastConnectionEnd"},
        {title: "Connected", key: "connected"},
        {title: "Connection interrupted", key: "connectionInterrupted"},
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
    const loadAgents = async function () {
      loading.value = true;
      const res = await fetch("/api/agent");
      if (!res.ok) {
        alert(await res.text());
      } else {
        agents.value = JSON.parse(await res.text());
        await filterAgents();
      }
      loading.value = false
    }

    const filterAgents = async function () {
      console.log("Filtering agents...");
      filteredAgents.value = searchQuery.value == "" ? agents.value : agents.value.filter((agent: Agent) => {
        return (agent.id && agent.id.includes(searchQuery.value)) || (agent.user && agent.user.includes(searchQuery.value))
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
          alert(await res.text());
        } else {
          await loadAgents();
        }
      } catch (err) {
        alert(err)
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
          alert(await res.text());
        } else {
          const data = JSON.parse(await res.text())
          newAgentID.value = data.id
          await copyAgentID()
        }
      } catch (err) {
        alert(err)
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
  <v-card class="ma-10 pa-7">
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
                  <br/><br/>
                  <div>Please run the following command on the machine you want to install the agent
                    on.
                  </div>
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

</style>
