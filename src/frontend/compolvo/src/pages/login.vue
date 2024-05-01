<script setup lang="ts">
import LoginForm from "../components/LoginForm.vue";
</script>

<template>
  <div class="form-container">
    <LoginForm/>
  </div>
</template>
<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100vw;
  height: 100%;
}
</style>
