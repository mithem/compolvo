<template>
  <h1>Profile (+ Status)</h1>
  <v-btn
    @click="deleteAccount"
    :loading=loading
    color="red"
  >Delete account
  </v-btn>
</template>

<script setup lang="ts">
import {defineComponent, ref} from "vue";

const loading = ref(false)

defineComponent({
  name: "Profile",
  setup() {

  }
})

async function deleteAccount() {
  loading.value = true
  const me = await fetch("/api/user/me")
  const id = (await me.json()).id
  const res = await fetch("/api/user?id=" + id, {
    method: "DELETE"
  })
  loading.value = false
  if (res.ok) {
    document.location.pathname = "/"
  } else {
    alert(await res.text())
  }
}
</script>
