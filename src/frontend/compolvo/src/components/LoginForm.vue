<template>
  <v-col>
    <v-text-field
      v-model="email"
      :counter="50"
      label="E-Mail"
      hide-details
      required
    ></v-text-field>
    <v-text-field
      v-model="password"
      :counter="50"
      label="Password"
      hide-details
      required
    >
    </v-text-field>
    <v-btn @click="login">Submit</v-btn>
  </v-col>
</template>

<style scoped>
</style>
<script setup lang="ts">
import {defineComponent} from "vue";

defineComponent({
  name: 'LoginForm',
  setup() {
  }
});

function login() {
  fetch("http://localhost:8000/auth", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: "test@example.com",
      password: "test"
    })
  }).then(res => {
    res.json().then(data => {
      const token = data.access_token;
    })
  })
}
</script>
