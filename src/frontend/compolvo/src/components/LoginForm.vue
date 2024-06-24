<template>
  <div class="form-card-container">
    <v-card class="form-card" title="Login">
      <v-card-item v-if="error != null">
        <ErrorPanel :error=error />
      </v-card-item>
      <v-form @submit.prevent="login">
        <v-col>
          <v-text-field
            type="email"
            class="vert-input-field"
            v-model="email"
            :counter="50"
            label="E-Mail"
            hide-details
            required
          ></v-text-field>
          <v-text-field
            type="password"
            class="vert-input-field"
            v-model="password"
            :counter="50"
            label="Password"
            hide-details
            required
          >
          </v-text-field>
          <v-btn
            type="submit"
            class="vert-input-field mt-5"
            :loading=loading
          >Submit
          </v-btn>
          <br/>
          <v-row>
            <RouterLink class="link" to="/register">No account yet?</RouterLink>
            <v-spacer></v-spacer>
            <span class="link" @click="triggerPasswordReset">
              Forgot password?
            </span>
          </v-row>
        </v-col>
      </v-form>
    </v-card>
  </div>
</template>

<style scoped>
.form-card-container {
  min-width: 200px;
  width: 40vw;
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  top: -10rem;
}
</style>
<script lang="ts">
import {defineComponent, ref} from "vue";
import Constants from "./Constants";


export default defineComponent({
  name: 'LoginForm',
  setup() {
    const loading = ref(false)
    const email = ref("")
    const password = ref("")
    const error = ref(null)

    const login = async function () {
      loading.value = true
      error.value = null
      const params = new URLSearchParams(window.location.search)
      let redirUrl = params.get("redirect_url");
      if (redirUrl === "/") {
        redirUrl = "/home"
      }
      const redirectUrl = redirUrl || (Constants.HOST_URL + "/home")
      try {
        const res = await fetch(Constants.HOST_URL + "/api/login?redirect_url=" + redirectUrl + "&email=" + encodeURIComponent(email.value) + "&password=" + encodeURIComponent(password.value));
        if (res.ok) {
          document.location.href = redirectUrl
        } else {
          error.value = new Error(await res.text())
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const triggerPasswordReset = async function () {
      loading.value = true
      error.value = null
      try {
        const res = await fetch(Constants.HOST_URL + "/api/user/password/reset", {
          method: "POST",
          body: JSON.stringify({email: email.value})
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    return {email, password, loading, error, login, triggerPasswordReset}
  },
});
</script>
