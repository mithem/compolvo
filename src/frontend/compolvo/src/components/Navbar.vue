<template>
  <v-toolbar class="navbar">
    <v-toolbar-title style="cursor: pointer" @click="$router.push('/')">Compolvo</v-toolbar-title>
    <v-toolbar-items>
      <div>
        <v-switch
          inline
          style="margin-top: 4px"
          v-model="themeMode"
          true-value="dark"
          false-value="light"
          indeterminate
          prepend-icon="mdi-theme-light-dark"
        >
        </v-switch>
      </div>
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

    function getCookieValue(name) {
      // Retrieve all cookies from the document
      let cookieArray = document.cookie.split(';');
      console.log(cookieArray);

      // Find the specific cookie by name
      let cookieValue = cookieArray.find(cookie => cookie.trim().startsWith(name + '='));

      if (!cookieValue) {
        return null; // Return null if the cookie is not found
      }

      // Extract only the value part of the cookie
      let value = cookieValue.split('=')[1];

      // Decode and parse the JSON value
      let decodedValue = decodeURIComponent(value);
      let parsedValue = JSON.parse(decodedValue);

      return parsedValue;
    }

    function getCookieExpiration(name) {
      let cookieData = getCookieValue(name);
      if (cookieData && cookieData.expires) {
        return new Date(cookieData.expires);
      }
      return null; // Return null if no expiration is found
    }

    let expirationDate = getCookieExpiration("token");
    console.log(expirationDate);

    return {theme, themeMode, darkMediaQuery, autoThemeHandler, getCookieExpiration, getCookieValue};
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
.theme-toggle {
  height: 100%;
}

.theme-toggle > div {
  height: 100%;
}

.navbar {
  z-index: 1;
}
</style>
