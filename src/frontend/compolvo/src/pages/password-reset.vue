<template>
  <v-card class="form-container">
    <v-card-title>Password reset</v-card-title>
    <v-progress-linear indeterminate v-if="resetting"></v-progress-linear>
    <div v-if="error !== null">
      <ErrorPanel :error="error"></ErrorPanel>
    </div>
    <v-form @submit.prevent="validate" fast-fail validate-on="input" ref="form">
      <v-col>
        <v-text-field
          type="password"
          class="vert-input-field"
          v-model="password"
          :counter="50"
          label="Password"
          :rules="passwordValidation"
          validate-on="input"
          required
        >
        </v-text-field>
        <v-text-field
          type="password"
          class="vert-input-field"
          v-model="repeatPassword"
          :counter="50"
          label="Repeat password"
          :rules="repeatPasswordValidation"
          validate-on="input"
          required
        >
        </v-text-field>
        <v-btn
          type="submit"
          :loading=resetting
        >Submit
        </v-btn>
      </v-col>
    </v-form>
  </v-card>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, ref} from "vue"
import {evaluatePasswordRules} from "../components/utils"

export default defineComponent({
  data: () => ({
    passwordValidation: [
      value => {
        return evaluatePasswordRules(value)
      }
    ],
  }),
  setup() {
    const password = ref("")
    const repeatPassword = ref("")
    const resetting = ref(false)
    const instance = getCurrentInstance()
    const error = ref<Error | null>(null)

    const repeatPasswordValidation = [
      value => {
        if (value !== password.value) {
          return "Passwords do not match"
        }
        return true
      }
    ]

    async function setPassword() {
      resetting.value = true
      try {
        const res = await fetch("/api/user/password", {
          method: "PATCH",
          body: JSON.stringify({
            reset_token: instance.proxy.$route.query.reset_token,
            password: password.value
          })
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          instance.proxy.$router.push("/login")
        }
      } catch (err) {
        error.value = err
      }
      resetting.value = false
    }

    async function validate() {
      const {valid: valid, errors: errors} = await instance.proxy.$refs.form.validate()
      if (valid) {
        await setPassword()
      } else {
        error.value = new Error("Error(s) valdiating form: " + errors.flatMap(err => err.errorMessages).join(", "))
      }
    }

    return {
      password,
      repeatPassword,
      repeatPasswordValidation,
      resetting,
      error,
      validate
    }
  }
})
</script>

<style scoped>

</style>
