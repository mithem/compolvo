<template>
  <filter_panel/>
  <v-container>{{ data }}</v-container>
  <v-container>
    <v-row>
      <v-col cols="12" md="6" lg="4" v-for="service in services" :key="service.id">
        <compact-card
          :serviceName="service.name"
          :serviceVersion="service.version"
          :serviceDescription="service.description"
          :license="service.license"
          :serviceImage="service.image"
          :tags="service.tags"
          :downloads="service.downloads"
          :price="service.price"
        />
      </v-col>
    </v-row>
  </v-container>

</template>
<script lang="ts">
import { defineComponent } from 'vue';
import CompactCard from '/src/components/compact_card.vue';
import {onMounted, ref} from "vue";

const data = ref(null);
const api_host = "https://localhost:8000/api/"

const fetchSpell = async () => {
  try {
    const response = await fetch(api_host + 'service');
    data.value = await response.json();
  } catch (error) {
    console.error(error);
  }
}
onMounted(fetchSpell);

export default defineComponent({
  components: {
    CompactCard
  },
  data() {
    return {
      services: [
        {
          id: 1,
          name: "Example Service",
          version: "1.0.0",
          description: "This is an example of a compact card component in Vue using Vuetify.",
          license: "MIT",
          image: "https://cdn.vuetifyjs.com/images/cards/sunshine.jpg",
          tags: ["Web", "API", "Tech"],
          downloads: 1500,
          price: "$19.99"
        },
        {
          id: 2,
          name: "Example Service",
          version: "1.0.0",
          description: "This is an example of a compact card component in Vue using Vuetify.",
          license: "MIT",
          image: "https://cdn.vuetifyjs.com/images/cards/sunshine.jpg",
          tags: ["Web", "API", "Tech"],
          downloads: 1500,
          price: "$19.99"
        },
        {
          id: 3,
          name: "Example Service",
          version: "1.0.0",
          description: "This is an example of a compact card component in Vue using Vuetify.",
          license: "MIT",
          image: "https://cdn.vuetifyjs.com/images/cards/sunshine.jpg",
          tags: ["Web", "API", "Tech"],
          downloads: 1500,
          price: "$19.99"
        },
        {
          id: 4,
          name: "Example Service",
          version: "1.0.0",
          description: "This is an example of a compact card component in Vue using Vuetify.",
          license: "MIT",
          image: "https://cdn.vuetifyjs.com/images/cards/sunshine.jpg",
          tags: ["Web", "API", "Tech"],
          downloads: 1500,
          price: "$19.99"
        },
      ]
    }
  }
});
</script>

<style scoped>
</style>
