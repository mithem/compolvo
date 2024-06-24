<template>
  <v-container>
    <v-alert type="error">
      <v-row>
        <v-col class="grow">
          Verification token expired
        </v-col>
        <v-col class="shrink">
          <EmailVerificationButton text="Resend verification mail"></EmailVerificationButton>
        </v-col>
      </v-row>
    </v-alert>
  </v-container>
</template>

<script lang="ts">
import {defineComponent, ref} from 'vue';
import EmailVerificationButton from "../../components/EmailVerificationButton.vue";

export default defineComponent({
  components: {EmailVerificationButton},
  setup() {
    const sendingEmail = ref(false)
    const error = ref<Error | null>(null)

    const sendEmail = async () => {
      sendingEmail.value = true
      try {
        const res = await fetch("/api/user/email/verify", {
          method: "POST"
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        }
      } catch (e) {
        error.value = e
      }
      sendingEmail.value = false
    }

    return {sendingEmail, error, sendEmail}
  }
})
</script>

<style scoped>

</style>
