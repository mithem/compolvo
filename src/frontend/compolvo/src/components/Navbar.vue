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
      <!-- Countdown Timer -->
      <span :class="['countdown', { 'text-red': countdown === 'Expired' }]">{{ countdown }}</span>
    </v-toolbar-items>
  </v-toolbar>
</template>

<script lang="ts">

import {ref} from "vue";
import {useTheme} from "vuetify";
import Constants from "./Constants";
import {License, Token} from "./models";

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
    const apiHost = Constants.HOST_URL + "/api/";
    const theme = useTheme();
    const themeMode = ref(localStorage.getItem("compolvo-theme") || "auto");
    const token = ref<Token>()
    const countdown = ref('');
    let timerInterval;

    const autoThemeHandler = (query) => {
      theme.global.name.value = query.matches ? "dark" : "light"
    }
    const darkMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const fetchTokenData = async () => {
      try {
        const response = await fetch(`${apiHost}auth/token`);
        if (response.ok) {
          token.value = await response.json().then((token) => {
            return {
              id: token.id as string,
              expires: new Date(token.expires),
            }
          })
          console.log("Token", token.value);  // Debugging line to see what's fetched
          updateCountdown()
        } else {
          alert(await response.text());
        }
      } catch (err) {
        alert(err);
      }
    }

    const updateCountdown = () => {
      const now = new Date();
      const timeLeft = token.value.expires.getTime() - now.getTime(); // Time left in milliseconds
      console.log(token.value.expires.getTime(),  now.getTime(), timeLeft)

      if (timeLeft > 0) {
        const seconds = Math.floor((timeLeft / 1000) % 60);
        const minutes = Math.floor((timeLeft / (1000 * 60)) % 60);
        const hours = Math.floor((timeLeft / (1000 * 60 * 60)) % 24);
        countdown.value = `${hours}h ${minutes}m ${seconds}s`;
      } else {
        countdown.value = "Expired";
        clearInterval(timerInterval); // Stop the timer when expired
      }
    };
    return {theme, themeMode, darkMediaQuery, autoThemeHandler, fetchTokenData,updateCountdown,countdown};
  },
  mounted() {
    this.fetchTokenData()
    this.setMenuItems()
    if (this.themeMode === "auto" || this.themeMode === null) {
      this.darkMediaQuery.addEventListener("change", this.autoThemeHandler)
    } else {
      this.theme.global.name.value = this.themeMode
    }

    this.timerInterval = setInterval(this.updateCountdown, 1000)
  },
  unmounted() {
    clearInterval(this.timerInterval)
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
.countdown {
  align-content: center
}
</style>
