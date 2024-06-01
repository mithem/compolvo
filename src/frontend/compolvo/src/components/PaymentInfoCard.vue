<template>
  <div class="container container-vert">
    <div class="container container-horiz">
  <v-card class="payment-detail-card">
    <v-card-title>Payment info</v-card-title>
    <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
    <ErrorPanel v-if="error !== null" :error="error"></ErrorPanel>
    <div id="card-element"></div>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="createPaymentMethod">Submit</v-btn>
    </v-card-actions>
  </v-card>
    </div>
  </div>
</template>

<script lang="ts">
import {getCurrentInstance, onMounted, ref} from "vue";
import Constants from "./Constants";
import type {
  PaymentMethod,
  Stripe as StripeType,
  StripeCardElement,
  StripeElements,
} from "@stripe/stripe-js"

declare var Stripe: StripeType

export default {
  name: 'PaymentInfoCard',
  props: {
    redirectPath: {
      type: String || null,
      default: null
    }
  },
  setup(props: {redirectPath: string | null}) {
    let stripe: typeof Stripe
    let elements: StripeElements
    let cardElement: StripeCardElement
    const loading = ref(false);
    const instance = getCurrentInstance()
    const error = ref<Error | null>(null)

    const initStripe = async function () {
      let stripeScript = document.createElement("script")
      stripeScript.src = "https://js.stripe.com/v3/"
      document.head.appendChild(stripeScript)
      stripeScript.addEventListener("load", () => {
        stripe = Stripe(Constants.STRIPE_PUBLISHABLE_API_KEY)
        elements = stripe.elements()
        cardElement = elements.create("card")
        cardElement.mount("#card-element")
      })
    }

    async function attachPaymentMethod(paymentMethod: PaymentMethod) {
      const res = await fetch("/api/billing/payment/method/attach", {
        method: "POST",
        body: JSON.stringify({
          method_id: paymentMethod.id
        })
      })
      if (!res.ok) {
        error.value = Error("Failed to attach payment method: " + await res.text())
      } else {
        if (props.redirectPath !== null) {
          instance.proxy.$router.push({path: props.redirectPath})
        } else {
          instance.proxy.$emit("attachment-successful")
        }
      }
      loading.value = false
    }

    const createPaymentMethod = async function () {
      event.preventDefault()
      loading.value = true
      const {paymentMethod, error: err} = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement
      });
      if (err) {
        error.value = Error(err.message)
        loading.value = false
      } else {
        await attachPaymentMethod(paymentMethod);
      }
    }

    onMounted(initStripe)

    return {loading, error, createPaymentMethod}
  }
}
</script>

<style scoped>
#card-element {
  margin: 10px;
  padding: 10px;
  min-height: 50px;
}

.payment-detail-card {
  width: 50vw;
}
.container {
  display: flex;
}

.container-vert {
  flex-direction: column;
  margin: 20px;
}

.container-horiz {
  justify-content: center;
}

</style>
