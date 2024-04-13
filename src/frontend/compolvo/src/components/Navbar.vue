<script setup lang="ts"></script>

<template>
  <v-toolbar>
    <v-toolbar-title style="cursor: pointer" @click="$router.push('/')">Compolvo</v-toolbar-title>
    <v-toolbar-items>
      <v-btn
        v-for="item in menuItems"
        :key="item.title"
        :to="{path: item.path}">
        <v-icon left dark class="mr-2">{{ item.icon }}</v-icon>
        {{ item.title }}
      </v-btn>
    </v-toolbar-items>
  </v-toolbar>
</template>

<script>
export default {
  name: "Compolvo",
  data() {
    return {
      appTitle: "Compolvo",
      sidebar: false,
      menuItems: [
        {title: "Home", path: "/home", icon: "mdi-home"},
        {title: "Compare", path: "/compare", icon: "mdi-scale-balance"},
        {title: "Profile", path: "/profile", icon: "mdi-account"},
        {title: "Login", path: "/login", icon: "mdi-account"}
      ]
    }
  }
}
</script>

<style scoped>

</style>
