<script lang="ts">
import {defineComponent, onMounted, ref} from "vue"
import {isHigherVersion} from "./utils"
import {AgentSoftware} from "./models";

export default defineComponent({
  props: ["software"],
  setup(props: { software: AgentSoftware }) {
    const software = ref(props.software);
    const upgrading = ref(false);
    const updateAvailable = ref(false);
    const iconName = ref<string>(software.value.agent.connected ? "mdi-check-circle" : "mdi-cancel");
    const iconColor = ref<string>(software.value.agent.connected ? "success" : "red");

    const startUpdate = async function () {
      // TODO: Actually start upgrade process
      upgrading.value = true;
      setTimeout(() => {
        upgrading.value = false;
      }, 5000);
    }

    const checkForUpdate = function () {
      updateAvailable.value = isHigherVersion(software.value.latest_version, software.value.installed_version)
    }

    onMounted(checkForUpdate)

    return {software, updateAvailable, upgrading, iconName, iconColor, startUpdate, checkForUpdate};
  }
});
</script>

<template>
  <v-card class="software-card">
    <v-card-title>
      {{ software.service.name }}
    </v-card-title>
    <v-card-subtitle>
      <div class="subtitle-container">
        <span v-if="software.agent.name !== null">{{ software.agent.name }}</span>
        <span v-else>{{ software.agent.id }}</span>
        <v-icon class="ml-2" :color="iconColor">{{ iconName }}</v-icon>
      </div>
    </v-card-subtitle>
    <v-card-text>
      <span v-if="software.installed_version != null">Installed: {{
          software.installed_version
        }}<br/></span>
      <span v-if="software.latest_version != null">Latest: {{
          software.service.latest_version
        }}</span>
    </v-card-text>
    <v-card-actions :v-if="updateAvailable">
      <v-spacer></v-spacer>
      <v-btn
        v-if="updateAvailable"
        @click="startUpdate"
        :loading="upgrading"
        color="blue">
        Update
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.software-card {
  padding: 8px;
}

.subtitle-container {
  align-items: center;
  display: flex;
}
</style>
