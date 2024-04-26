<script lang="ts">
import {defineComponent, onMounted} from "vue"
import type {
  Stripe as StripeType,
  StripeCardElement,
  StripeElements,
  StripeElementsOptionsMode
} from "@stripe/stripe-js"

declare var Stripe: StripeType

export default defineComponent({
  setup() {
    let stripe: typeof Stripe
    let elements: StripeElements
    let cardElement: StripeCardElement
    const initStripe = async function () {
      let stripeScript = document.createElement("script")
      stripeScript.src = "https://js.stripe.com/v3/"
      document.head.appendChild(stripeScript)
      stripeScript.addEventListener("load", () => {
        stripe = Stripe("pk_test_51P9pWbCe34F7lARi5YbIkswtMqlWNwrYrA9BYpBwyJXv4OyfPtLiC8zzPC3I0HoY4R0aQyrlKgAtbTuTYHstVrX800secrzlBA")
        const options: StripeElementsOptionsMode = {
          mode: "payment",
          amount: 1099,
          currency: "eur"
        }
        elements = stripe.elements(options)
        cardElement = elements.create("card")
        cardElement.mount("#card-element")
      })
    }

    const createPaymentMethod = async function () {
      event.preventDefault()
      const {paymentMethod, error} = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement
      });
      if (error) {
        alert(error.message)
        return;
      }
      const res = await fetch("/api/billing/payment/method/attach", {
        method: "POST",
        body: JSON.stringify({
          method_id: paymentMethod.id
        })
      })
      if (!res.ok) {
        alert(await res.text())
      } else {
        alert("Success")
      }
      /*const {error: err} = await elements.submit();
      if (err) {
        alert(err);
        return;
      }

      const res = await fetch("/api/billing/payment/intent", {
        method: "POST"
      })
      if (!res.ok) {
        alert(await res.text())
        return;
      }
      const {client_secret: clientSecret} = await res.json()
      const {error} = await stripe.confirmPayment({
        elements,
        clientSecret,
        confirmParams: {
          return_url: "http://localhost:8080"
        }
      })
      if (error) {
        alert(error)
      }*/
    }

    onMounted(initStripe)

    return {createPaymentMethod}
  }
})
</script>

<template>
  <div class="container container-vert">
    <h1>Payment info</h1>
    <div class="container container-horiz">
      <v-card class="payment-detail-card">
        <div id="card-element"></div>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="createPaymentMethod">Submit</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

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
