<script lang="ts">
import {defineComponent, ref} from "vue"
import {ServiceOffering} from "../components/models";
import {useTheme} from "vuetify";

export default defineComponent({
  props: ["offering"],
  setup(props: { offering: ServiceOffering }) {
    console.log("offering:", props.offering)
    const offering = props.offering
    const intervals = [
      ["year", 360],
      ["month", 30],
      ["day", 1]
    ]
    let intervalName: string
    let divisor: number
    for (const interval of intervals) {
      if (offering.duration_days >= (interval[1] as number)) {
        intervalName = interval[0] as string
        divisor = interval[1] as number
        break
      }
    }
    const formattedNameValue = (offering.duration_days / divisor).toString() + " " + intervalName + " offering"

    const formattedName = ref<string>(formattedNameValue);
    const showingSnackbar = ref(false);
    const snackbarText = ref("");
    const creating = ref(false);
    const theme = useTheme();

    const createServicePlan = async function () {
      creating.value = true;
      try {
        const res = await fetch("/api/service/plan", {
          method: "POST",
          body: JSON.stringify({
            service_offering: offering.id
          })
        })
        if (!res.ok) {
          alert(await res.text())
        } else {
          snackbarText.value = "Order successful. Go to profile to install it on your agents."
          showingSnackbar.value = true;
        }
      } catch (err) {
        alert(err)
      }
      creating.value = false;
    }

    return {
      offering,
      formattedName,
      snackbarText,
      showingSnackbar,
      creating,
      theme,
      createServicePlan
    }
  },
  watch: {
    offering(value) {
      this.formattedName = this.formatName(value);
    }
  }
})
</script>

<template>
  <v-card class="offering-card">
    <v-card-title>{{ formattedName }}</v-card-title>
    <v-progress-linear v-if="creating" indeterminate></v-progress-linear>
    <v-card-text>
      €{{ offering.price }} for {{ offering.duration_days }} days<br/>
      Your subscription will automatically renew.
    </v-card-text>
    <div class="cta-container">
      <v-btn color="blue" prepend-icon="mdi-cart" @click="createServicePlan">
        Buy now
      </v-btn>
    </div>
  </v-card>


  <v-snackbar
    v-model="showingSnackbar"
    color="success"
  >
    {{ snackbarText }}
    <template v-slot:actions>
      <v-btn
        variant="text"
        @click="showingSnackbar=false"
      >
        Close
      </v-btn>
    </template>
  </v-snackbar>
</template>

<style scoped>
.offering-card {
  padding-bottom: 10px;
  height: 100%; /* So all cards in slide group are the same height */
  display: flex;
  flex-direction: column;
  min-width: 20vw;
  background-color: rgb(var(--v-theme-second-layer-card-background));
}

.cta-container {
  display: flex;
  justify-content: center;
}
</style>
