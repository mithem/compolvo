<template>
  <v-app>
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
body, #app, .v-application {
  background-color: #E0E0E0; /* Light grey background; change hex as needed */
}
</style>
<style src="@/styles/global.scss"></style>
