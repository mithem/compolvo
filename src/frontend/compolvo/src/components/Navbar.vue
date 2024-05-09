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
  <v-snackbar color="error" v-model="showingErrorSnackbar">
    {{ error.message }}
    <template v-slot:actions>
      <v-btn
        variant="text"
        @click="showingErrorSnackbar = false"
      >Close
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script lang="ts">

import {getCurrentInstance, ref} from "vue";
import {useTheme} from "vuetify";
import Constants from "./Constants";
import {Token} from "./models";

export default {
  name: "Compolvo",
  data() {
    return {
      appTitle: "Compolvo",
      sidebar: true
    }
  },
  setup() {
    const apiHost = Constants.HOST_URL + "/api/";
    const theme = useTheme();
    const themeMode = ref(localStorage.getItem("compolvo-theme") || "auto");
    const token = ref<Token>()
    const countdown = ref('');
    let timerInterval;
    const menuItems = ref<{ title: string, path: string, icon: string }[]>([]);
    const error = ref<Error | null>(null);
    const instance = getCurrentInstance().proxy
    const showingErrorSnackbar = ref(false);

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
        }
        await updateCountdown() // Update with "expired" if no valid token was retrieved
      } catch (err) {
        error.value = err
        showingErrorSnackbar.value = true
      }
    }

    const isLoggedIn = async () => {
      try {
        const res = await fetch("/api/user/me")
        if (!res.ok) {
          return false
        }
        const data = JSON.parse(await res.text())
        return data.id !== undefined
      } catch (err) {
        error.value = err
        showingErrorSnackbar.value = true
      }
    }

    const setMenuItems = async () => {
      let items = []
      if (await isLoggedIn()) {
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
            query: {redirect_url: instance.$route.fullPath},
            icon: "mdi-account"
          }
        )
      }
      menuItems.value = items;
    }

    const updateCountdown = async () => {
      const now = new Date();
      const timeLeft = token.value !== undefined ? token.value.expires.getTime() - now.getTime() : -1; // Time left in milliseconds

      if (timeLeft > 0) {
        const seconds = Math.floor((timeLeft / 1000) % 60);
        const minutes = Math.floor((timeLeft / (1000 * 60)));
        countdown.value = `${minutes}m ${seconds}s`;
      } else {
        countdown.value = "Expired";
        clearInterval(timerInterval); // Stop the timer when expired
        // Reset only if menu bar shows restricted pages (in order to not spam the auth check endpoint each time this method gets called)
        if (menuItems.value.length >= 1) {
          await setMenuItems()
        }
      }
    };
    return {
      theme,
      themeMode,
      darkMediaQuery,
      countdown,
      menuItems,
      showingErrorSnackbar,
      error,
      autoThemeHandler,
      fetchTokenData,
      updateCountdown,
      setMenuItems
    };
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
  align-content: center;
  margin-right: 20px;
}
</style>
