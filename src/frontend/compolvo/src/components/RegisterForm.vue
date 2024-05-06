<template>
  <div class="card-container">
    <v-card class="form-card" title="Register">
      <v-card-item v-if="error != null">
        <ErrorPanel :error=error />
      </v-card-item>
      <v-form @submit.prevent="validate" fast-fail validate-on="input" ref="form">
        <v-col>
          <v-row
            class="vert-input-field"
          >
            <v-text-field
              class="horiz-input-field"
              v-model="firstName"
              :counter="100"
              label="First name"
            ></v-text-field>
            <v-text-field
              class="horiz-input-field"
              v-model="lastName"
              :counter="100"
              label="Last name"
            ></v-text-field>
          </v-row>
          <v-text-field
            type="email"
            class="vert-input-field"
            v-model="email"
            :counter="50"
            label="E-Mail"
            required
          ></v-text-field>
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
            :loading=loading
          >Submit
          </v-btn>
        </v-col>
      </v-form>
    </v-card>
  </div>
</template>

<style scoped>
</style>
<script lang="ts">
import {defineComponent, getCurrentInstance, ref} from "vue";
import Constants from "./Constants";
import {evaluatePasswordRules} from "./utils";


export default defineComponent({
  name: 'RegisterForm',
  data: () => ({
    passwordValidation: [
      value => {
        return evaluatePasswordRules(value)
      }
    ]
  }),
  setup() {
    const loading = ref(false)
    const firstName = ref("")
    const lastName = ref("")
    const email = ref("")
    const password = ref("")
    const repeatPassword = ref("")
    const repeatPasswordValidation = [
      value => {
        if (value !== password.value) {
          return "Passwords don't match."
        }
        return true
      }
    ]
    const error = ref<Error | null>(null);

    const instance = getCurrentInstance().proxy

    async function validate() {
      const {valid: valid, errors: errors} = await instance.$refs.form.validate()
      if (valid) {
        await register()
      } else {
        error.value = new Error("Error(s) valdiating form: " + errors.flatMap(err => err.errorMessages).join(", "))
      }
    }

    async function register() {
      loading.value = true
      const res = await fetch(Constants.HOST_URL + "/api/user", {
        method: "POST",
        body: JSON.stringify({
          first_name: firstName.value != "" ? firstName.value : null,
          last_name: lastName.value != "" ? lastName.value : null,
          email: email.value,
          password: password.value
        })
      })
      loading.value = false
      if (res.ok) {
        document.location.pathname = "/";
      } else {
        error.value = new Error(await res.text())
      }
    }

    return {
      firstName,
      lastName,
      email,
      password,
      repeatPassword,
      loading,
      repeatPasswordValidation,
      error,
      validate,
      register
    }
  },
});
</script>
