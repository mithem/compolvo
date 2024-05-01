<template>
  <v-toolbar>
    <v-toolbar-title style="cursor: pointer" @click="$router.push('/')">Compolvo</v-toolbar-title>
    <v-toolbar-items>
      <v-switch
        v-model="themeMode"
        true-value="dark"
        false-value="light"
        indeterminate
        prepend-icon="mdi-theme-light-dark"
      >
      </v-switch>
      <v-btn
        v-for="item in menuItems"
        :key="item.title"
        :to="{path: item.path, query: item.query }">
        <v-icon left dark class="mr-2">{{ item.icon }}</v-icon>
        {{ item.title }}
      </v-btn>
    </v-toolbar-items>
  </v-toolbar>
</template>

<script lang="ts">

import {ref} from "vue";
import {useTheme} from "vuetify";

export default {
  name: "Compolvo",
  data() {
    return {
      appTitle: "Compolvo",
      sidebar: true,
      menuItems: []
    }
  },
  setup() {
    const theme = useTheme();
    const themeMode = ref(localStorage.getItem("compolvo-theme") || "auto");

    const autoThemeHandler = (query) => {
      theme.global.name.value = query.matches ? "dark" : "light"
    }
    const darkMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    return {theme, themeMode, darkMediaQuery, autoThemeHandler}
  },
  mounted() {
    this.setMenuItems()
    if (this.themeMode === "auto" || this.themeMode === null) {
      this.darkMediaQuery.addEventListener("change", this.autoThemeHandler)
    } else {
      this.theme.global.name.value = this.themeMode
    }
  },
  watch: {
    themeMode(scheme) {
      if (scheme != null) {
        localStorage.setItem("compolvo-theme", scheme)
      }
      this.darkMediaQuery.removeEventListener("change", this.autoThemeHandler)
      if (scheme === "auto") {
        this.darkMediaQuery.addEventListener("change", this.autoThemeHandler)
      } else {
        this.theme.global.name.value = scheme
      }
    }
  },
  methods: {
    async isLoggedIn(): Promise<boolean> {
      try {
        const res = await fetch("/api/user/me")
        if (!res.ok) {
          return false
        }
        const data = JSON.parse(await res.text())
        return data.id !== undefined
      } catch (err) {
        return false
      }
    },
    async setMenuItems() {
      let items = []
      if (await this.isLoggedIn()) {
        items.push(
          {title: "Home", path: "/home", icon: "mdi-home"},
          {title: "Compare", path: "/compare", icon: "mdi-scale-balance"},
          {title: "Agents", path: "/agents", icon: "mdi-dns"},
          {title: "Profile", path: "/profile", icon: "mdi-account"},
          {title: "Logout", path: "/logout", "icon": "mdi-account"}
        )
      } else {
        items.push(
          {
            title: "Login",
            path: "/login",
            query: {redirect_url: this.$route.fullPath},
            icon: "mdi-account"
          }
        )
      }
      this.menuItems = items;
    }
  }
}
</script>

<style scoped>
</style>
