<template>
  <div class="page-container">
    <div class="page-container-cell">
      <div class="compolvo-container">
        <h1>{{ pageTitle }}</h1>
        <p>Willkommen auf der Compolvo-Seite!</p>
      </div>
      <div class="image-container">
        <img src="@/assets/logo_compolvo.png" alt="Bildbeschreibung" class="styled-image">
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref} from 'vue';

// Definiere den Seitentitel
const pageTitle = ref('Compolvo');

// Hier kannst du weitere Logik hinzufügen, falls benötigt
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100vw;
}

.page-container-cell {
  height: fit-content;
  position: relative;
  top: -10rem;
}

.compolvo-container {
  text-align: center;
  margin-top: 50px;
  position: relative;
}

h1 {
  font-size: 3rem;
  color: #1976d2; /* Beispiel Farbe */
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px; /* Höhe nach Bedarf anpassen */
}

.styled-image {
  max-width: 100%; /* Bildgröße anpassen */
  max-height: 100%; /* Bildgröße anpassen */
  border-radius: 10px; /* Runde Ecken */
}

</style>
