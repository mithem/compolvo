<template>
  <div class="card-container">
    <v-card class="form-card">
      <v-form @submit.prevent="login">
        <v-col>
          <v-text-field
            class="vert-input-field"
            v-model="email"
            :counter="50"
            label="E-Mail"
            hide-details
            required
          ></v-text-field>
          <v-text-field
            class="vert-input-field"
            v-model="password"
            :counter="50"
            label="Password"
            hide-details
            required
          >
          </v-text-field>
          <v-btn
            type="submit"
            class="vert-input-field"
          >Submit
          </v-btn>
        </v-col>
      </v-form>
    </v-card>
  </div>
</template>

<style scoped>
.form-card {
  background-color: #f7f7f7;
  border: none;
  border-radius: 10px;
  padding: 10px;
  max-width: 400px;
  width: 40%;
  min-width: 200px;
  margin: 50px auto;
}

.vert-input-field {
  margin-bottom: 12px;
}

.card-container {
  width: 100%;
  height: 100%;
}
</style>
<script setup lang="ts">
import {defineComponent, ref} from "vue";
import Constants from "./Constants";

const email = ref("")
const password = ref("")

defineComponent({
  name: 'LoginForm',
  setup() {
    return {email, password}
  },
});

async function login() {
  const params = new URLSearchParams(window.location.search)
  const redirectUrl = params.get("redirect_url") || Constants.HOST_URL
  const res = await fetch(Constants.HOST_URL + "/api/login?redirect_url=" + redirectUrl + "&email=" + encodeURIComponent(email.value) + "&password=" + encodeURIComponent(password.value));
  if (res.ok) {
    document.location.href = redirectUrl
  } else {
    alert(await res.text())
  }
}
</script>
