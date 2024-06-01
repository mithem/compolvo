<script lang="ts">
import {defineComponent, getCurrentInstance, onMounted, ref} from "vue"
import type {
  Stripe as StripeType,
  StripeCardElement,
  StripeElements,
  StripeElementsOptionsMode
} from "@stripe/stripe-js"
import Constants from "../components/Constants";
import PaymentInfoCard from "../components/PaymentInfoCard.vue";

declare var Stripe: StripeType

export default defineComponent({
  components: {PaymentInfoCard},
  props: ["redirectPath"],
  setup() {
    return {}
  }
})
</script>

<template>
      <PaymentInfoCard redirect-path="profile" />
</template>

<style scoped>

</style>
