<script lang="ts">
import {defineComponent, getCurrentInstance, onMounted, ref} from "vue"
import {isHigherVersion} from "./utils"
import {AgentSoftware} from "./models";

export default defineComponent({
  props: ["software"],
  setup(props: { software: AgentSoftware }) {
    const software = ref(props.software);
    const upgrading = ref(false);
    const uninstalling = ref(false);
    const removing = ref(false)
    const updateAvailable = ref(false);
    const iconName = ref<string>(software.value.agent.connected ? "mdi-check-circle" : "mdi-cancel");
    const iconColor = ref<string>(software.value.agent.connected ? "success" : "red");
    const instance = getCurrentInstance();
    const staleTresholdDate = new Date()
    staleTresholdDate.setTime(staleTresholdDate.getTime() - 1000 * 60 * 60) // 1 hour ago
    const lastUpdated = props.software.last_updated !== null ? new Date(props.software.last_updated) : null;
    // lastUpdated === null means no status update every occured (e.g. installation while agent isn't running)
    const isStale = ref(lastUpdated === null || (props.software.installing || props.software.uninstalling) && lastUpdated < staleTresholdDate)
    const staleWarningTooltip = "No updates where received " + (lastUpdated ? "since " + lastUpdated.toLocaleString() + "." : "from agent (yet).")

    const startUpdate = async function () {
      upgrading.value = true;
      try {
        const res = await fetch("/api/agent/software/update?id=" + software.value.id, {
          method: "POST"
        })
        if (!res.ok) {
          alert(await res.text())
        } else {
          instance.proxy.$emit("reload")
        }
      } catch (err) {
        alert(err)
      }
      upgrading.value = false;
    }

    const checkForUpdate = function () {
      updateAvailable.value = isHigherVersion(software.value.latest_version, software.value.installed_version)
    }

    const uninstall = async function () {
      uninstalling.value = true;
      try {
        const res = await fetch("/api/agent/software/uninstall?id=" + software.value.id, {
          method: "DELETE"
        })
        if (!res.ok) {
          alert(await res.text())
        } else {
          instance.proxy.$emit("reload")
        }
      } catch (err) {
        alert(err)
      }
      uninstalling.value = false;
    }

    const remove = async function () {
      removing.value = true
      try {
        const res = await fetch("/api/agent/software?id=" + software.value.id, {
          method: "DELETE"
        })
        if (!res.ok) {
          alert(await res.text())
        } else {
          instance.proxy.$emit("reload")
        }
      } catch (err) {
        alert(err)
      }
      removing.value = false
    }

    onMounted(checkForUpdate)

    return {
      software,
      updateAvailable,
      upgrading,
      uninstalling,
      removing,
      iconName,
      iconColor,
      isStale,
      staleWarningTooltip,
      startUpdate,
      checkForUpdate,
      uninstall,
      remove
    };
  }
});
</script>

<template>
  <v-card class="software-card">
    <v-card-title>
      <div style="display: flex">
        {{ software.service.name }}
        <template v-if="isStale">
          <v-spacer></v-spacer>
          <v-tooltip :text="staleWarningTooltip">
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" color="warning" id="stale-warning">mdi-alert</v-icon>
            </template>
          </v-tooltip>
        </template>
      </div>
    </v-card-title>
    <v-card-subtitle>
      <div class="subtitle-container">
        <span v-if="software.agent.name !== null">{{ software.agent.name }}</span>
        <span v-else>{{ software.agent.id }}</span>
        <v-spacer></v-spacer>
        <span>
          {{ software.agent.connected ? "connected" : "disconnected" }}
        <v-icon class="ml-2" :color="iconColor">{{ iconName }}</v-icon>
        </span>
      </div>
    </v-card-subtitle>
    <v-card-text>
      <div v-if="software.installing || software.uninstalling">
        <span v-if="software.installing">
          Installing...
        </span>
        <span v-if="software.uninstalling">Uninstalling...</span>
        <v-progress-linear indeterminate>
        </v-progress-linear>
      </div>
      <div v-if="software.corrupt" style="color: red; font-weight: bold;">
        Corrupt
      </div>
      <span v-if="software.installed_version != null">Installed: {{
          software.installed_version
        }}<br/></span>
      <span v-if="software.latest_version != null">Latest: {{
          software.latest_version
        }}</span>
    </v-card-text>
    <v-card-actions>
      <v-btn
        v-if="isStale"
        @click="remove"
        :removing="removing"
        color="red"
        variant="outlined"
      >
        Dismiss
      </v-btn>
      <v-btn
        v-else
        @click="uninstall"
        :loading="uninstalling"
        color="red"
        variant="outlined"
        :disabled="software.uninstalling"
      >
        Uninstall
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        v-if="updateAvailable"
        @click="startUpdate"
        :loading="upgrading"
        :disabled="software.installing || software.uninstalling"
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
