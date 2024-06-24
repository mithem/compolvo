<template>
  <v-btn
    @click="verifyEmailAddress"
    :loading="verifyingEmail"
  >{{ props.text }}
  </v-btn>
  <v-snackbar :text="snackbarText" v-model="showingSnackbar" :color="snackbarType"></v-snackbar>
</template>

<script lang="ts">
import {defineComponent, ref} from "vue";

export default defineComponent({
  props: {text: String},
  setup(props: { text: String }) {
    const verifyingEmail = ref(false)
    const snackbarText = ref("")
    const showingSnackbar = ref(false)
    const snackbarType = ref("success")

    const showSnackbar = (text: string, type: string = "success") => {
      snackbarText.value = text
      snackbarType.value = type
      showingSnackbar.value = true
    }

    const verifyEmailAddress = async function () {
      verifyingEmail.value = true
      try {
        const res = await fetch("/api/user/email/verify", {
          method: "POST"
        })
        if (res.ok) {
          showSnackbar("Verification email sent.")
        } else {
          showSnackbar("Error: " + await res.text(), "error")
        }
      } catch (err) {
        showSnackbar("Error: " + err.toString(), "error")
      }
      verifyingEmail.value = false
    }

    return {
      props,
      verifyingEmail,
      showingSnackbar,
      snackbarText,
      snackbarType,
      verifyEmailAddress
    }
  }
})
</script>

<style scoped>

</style>
