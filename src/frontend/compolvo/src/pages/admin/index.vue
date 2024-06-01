<template>
  <v-col>
    <ErrorPanel v-if="error !== null" :error="error"></ErrorPanel>
    <v-data-table
      :headers="headers"
      :items="stati"
      item-key="server_id"
      class="elevation-1"
    >
      <template v-slot:top>
        <v-toolbar title="Server status">
          <v-btn
            @click="performBillingMaintenance"
            prepend-icon="mdi-wrench"
            :loading="stati.some(status => status.performing_billing_maintenance)"
          >
            Billing maintenance
          </v-btn>
          <v-btn
            color="warning"
            prepend-icon="mdi-database-arrow-up"
            @click="demoDbSetup"
          >Demo DB setup</v-btn>
        </v-toolbar>
      </template>
    </v-data-table>
  </v-col>
</template>

<script lang="ts">
import {defineComponent, ref} from "vue"
import {ServerStatus} from "../../components/models";
import {getWsEndpoint} from "../../components/utils";

export default defineComponent({
  data() {
    return {
      headers: [
        {title: "Server id", key: "server_id"},
        {title: "Running", key: "server_running"},
        {title: "Billing maintenance", key: "performing_billing_maintenance"},
      ]
    }
  },
  setup() {
    const setupRunning = ref(false)
    const error = ref<Error | null>(null)
    const stati = ref<ServerStatus[]>([])
    const ws = new WebSocket(getWsEndpoint("/api/notify"))

    const performBillingMaintenance = async function () {
      try {
        const res = await fetch("/api/billing/maintenance", {
          method: "POST"
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        }
      } catch (err) {
        error.value = err
      }
    }
    const demoDbSetup = async function () {
      setupRunning.value = true
      try {
        const res = await fetch("/api/setup", {
          method: "POST",
          body: JSON.stringify({
            services: true,
            service_offerings: true
          })
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        }
      } catch (err) {
        error.value = err
      }
      setupRunning.value = false
    }
    const fetchServerStati = async function () {
      try {
        const res = await fetch("/api/server-status")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          stati.value = await res.json()
        }
      } catch (err) {
        error.value = err
      }
    }

    const connectWS = function () {
      ws.onmessage = function (event) {
        const data = JSON.parse(event.data)
        if (data.event && data.event.type === "billing-maintenance") {
          fetchServerStati()
        }
      }
      ws.onopen = () => {
        ws.send(JSON.stringify({
          intent: "subscribe",
          event_type: "billing-maintenance",
          subscriber_type: "user"
        }))
      }
    }

    return {
      stati,
      error,
      setupRunning,
      fetchServerStati,
      performBillingMaintenance,
      connectWS,
      demoDbSetup
    }
  },
  mounted() {
    this.fetchServerStati()
    this.connectWS()
  }
})
</script>

<style scoped>

</style>
