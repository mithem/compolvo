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

<script lang="ts">

export default {
  name: "Compolvo",
  data() {
    return {
      appTitle: "Compolvo",
      sidebar: true,
      menuItems: [
      ]
    }
  },
  mounted() {
    this.setMenuItems()
  },
  methods: {
    async isLoggedIn(): Promise<boolean> {
      try {
        const res = await fetch("/api/user/me")
        const data = JSON.parse(await res.text())
        return data.id !== undefined
      } catch (err) {
        return false
      }
    },
    async setMenuItems() {
      if (await this.isLoggedIn()) {
        this.menuItems = [
          {title: "Home", path: "/home", icon: "mdi-home"},
          {title: "Compare", path: "/compare", icon: "mdi-scale-balance"},
          {title: "Profile", path: "/profile", icon: "mdi-account"},
          {title: "Logout", path: "/logout", "icon": "mdi-account"}
        ]
      } else {
        this.menuItems = [
          {
            title: "Login",
            path: "/login?redirect_url=" + document.location.pathname,
            icon: "mdi-account"
          }
        ]
      }
    }
  }
}
</script>

<style scoped>

</style>
