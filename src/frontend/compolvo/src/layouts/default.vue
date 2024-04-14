<template>
  <v-app>
    <Navbar/>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>

</script>

<style>
/* Global styles */
body, #app, .v-application {
  background-color: #E0E0E0;  /* Light grey background; change hex as needed */
}
</style>
