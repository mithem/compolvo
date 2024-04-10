<template>
  <div>
    <h1>Compare page</h1>
    <compact_card :spell="spell" />
    <v-container>{{ spell }}</v-container>
  </div>
</template>

<script setup lang="ts">
import Compact_card from "../components/compact_card.vue";
import {onMounted, ref} from "vue";

const spell = ref(null);
const api_host = "https://localhost:3000/api/"

const fetchSpell = async () => {
  try {
    const response = await fetch(api_host + 'service');
    spell.value = await response.json();
  } catch (error) {
    console.error(error);
  }
}
onMounted(fetchSpell);
</script>
