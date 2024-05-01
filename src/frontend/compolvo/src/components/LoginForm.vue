<template>
  <div class="form-card-container">
    <v-card class="form-card" title="Login">
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
          <RouterLink class="link" to="/register">No account yet?</RouterLink>
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
    const login = async function () {
      loading.value = true
      const params = new URLSearchParams(window.location.search)
      const redirectUrl = params.get("redirect_url") || Constants.HOST_URL
      try {
        const res = await fetch(Constants.HOST_URL + "/api/login?redirect_url=" + redirectUrl + "&email=" + encodeURIComponent(email.value) + "&password=" + encodeURIComponent(password.value));
        if (res.ok) {
          document.location.href = redirectUrl
        } else {
          alert(await res.text())
        }
      } catch (err) {
        alert(err);
      }
      loading.value = false
    }
    return {email, password, loading, login}
  },
});
</script>
