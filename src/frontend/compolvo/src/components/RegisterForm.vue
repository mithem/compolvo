<template>
  <div class="card-container">
    <v-card class="form-card">
      <v-form @submit.prevent="register">
        <v-col>
          <v-row
            class="vert-input-field"
          >
            <v-text-field
              class="horiz-input-field"
              v-model="firstName"
              :counter="100"
              label="First name"
              hide-details
            ></v-text-field>
            <v-text-field
              class="horiz-input-field"
              v-model="lastName"
              :counter="100"
              label="Last name"
              hide-details
            ></v-text-field>
          </v-row>
          <v-text-field
            type="email"
            class="vert-input-field"
            v-model="email"
            :counter="50"
            label="E-Mail"
            hide-details
            required
          ></v-text-field>
          <v-text-field
            type="password"
            class="vert-input-field"
            v-model="password"
            :counter="50"
            label="Password"
            hide-details
            required
          >
          </v-text-field>
          <v-text-field
            type="password"
            class="vert-input-field"
            v-model="repeatPassword"
            :counter="50"
            label="Repeat password"
            hide-details
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
<script setup lang="ts">
import {defineComponent, ref} from "vue";
import Constants from "./Constants";

const loading = ref(false)
const firstName = ref("")
const lastName = ref("")
const email = ref("")
const password = ref("")
const repeatPassword = ref("")

defineComponent({
  name: 'RegisterForm',
  setup() {
    return {firstName, lastName, email, password, repeatPassword}
  },
});

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
    alert(await res.text())
  }
}
</script>
