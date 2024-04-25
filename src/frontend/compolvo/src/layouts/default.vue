<template>
  <v-app id="app" style="height: 100vh">
    <Navbar/>
    <v-main>
      <router-view/>
    </v-main>
    <AppFooter/>
  </v-app>
</template>

<script lang="ts" setup>

</script>

<style>
/* Global styles */
html,body, #app, .v-application {
  background-color: #E0E0E0; /* Light grey background */
  max-height: 100vw;
  display: flex;
}
</style>
<style src="@/styles/global.scss"></style>

