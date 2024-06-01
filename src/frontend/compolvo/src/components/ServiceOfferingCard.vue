<script lang="ts">
import {defineComponent, ref} from "vue"
import {ServiceOffering} from "./models";
import {useTheme} from "vuetify";

export default defineComponent({
  props: ["offering"],
  setup(props: { offering: ServiceOffering }) {
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
    const snackbarColor = ref("success")
    const creating = ref(false);
    const theme = useTheme();
    const showingPaymentInfoCard = ref(false)

    const showSnackbar = function (message: string, color: string = "success") {
      snackbarText.value = message
      snackbarColor.value = color
      showingSnackbar.value = true
    }

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
          if (res.status === 402) { // requires payment details
            showingPaymentInfoCard.value = true
          } else {
            showSnackbar(await res.text(), "error")
          }
        } else {
          showSnackbar("Order successful. Go to profile to install it on your agents.")
        }
      } catch (err) {
        showSnackbar(err.toString(), "error")
      }
      creating.value = false;
    }

    const onPaymentMethodAttached = function() {
      showingPaymentInfoCard.value = false
      showSnackbar("Payment details added. Subscribing to service plan...")
      createServicePlan()
    }

    return {
      offering,
      formattedName,
      snackbarText,
      showingSnackbar,
      snackbarColor,
      creating,
      theme,
      showingPaymentInfoCard,
      createServicePlan,
      onPaymentMethodAttached
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
  <v-dialog v-model="showingPaymentInfoCard" location="top" >
    <PaymentInfoCard @attachment-successful="onPaymentMethodAttached()"/>
  </v-dialog>


  <v-snackbar
    v-model="showingSnackbar"
    :color="snackbarColor"
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
