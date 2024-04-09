<script setup lang="ts"></script>

<template>
  <v-toolbar>
    <v-toolbar-title :to="{path: '/index'}">Compolvo</v-toolbar-title>
    <v-toolbar-items>
      <v-btn :to="{path: '/something'}">
        Something
      </v-btn>
    </v-toolbar-items>
  </v-toolbar>
</template>

<style scoped>

</style>
