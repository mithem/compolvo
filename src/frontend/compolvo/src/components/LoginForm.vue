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
  window.location.href = "http://localhost:8000/api/login?redirect_url=http://" + window.location.host + "&email=" + encodeURIComponent("test@example.com") + "&password=" + encodeURIComponent("test");
}
</script>
