<template>
  <v-app id="app" style="height: 100vh; display: flex;">
    <Navbar/>
    <v-main style="display: flex; flex: 1">
      <router-view/>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>

</script>

<style src="@/styles/global.scss"></style>
<style src="@/styles/main.css"></style>

