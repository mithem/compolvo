<template>
  <filter_panel/>
  <v-btn @click="fetchData">Load Data</v-btn>
  <v-container>
    <div v-if="data">{{ data }}</div>
  </v-container>
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
import {defineComponent, ref} from 'vue';
import CompactCard from '@/components/compact_card.vue';
import Constants from "../components/Constants"; // Adjust the path as necessary

export default defineComponent({
  components: {
    CompactCard
  },
  setup() {
    const services = ref([
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
      },{
        id: 2,
        name: "Example Service",
        version: "1.0.0",
        description: "This is an example of a compact card component in Vue using Vuetify.",
        license: "MIT",
        image: "https://cdn.vuetifyjs.com/images/cards/sunshine.jpg",
        tags: ["Web", "API", "Tech"],
        downloads: 1500,
        price: "$19.99"
      },{
        id: 3,
        name: "Example Service",
        version: "1.0.0",
        description: "This is an example of a compact card component in Vue using Vuetify.",
        license: "MIT",
        image: "https://cdn.vuetifyjs.com/images/cards/sunshine.jpg",
        tags: ["Web", "API", "Tech"],
        downloads: 1500,
        price: "$19.99"
      },{
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
    ]);
    const data = ref(null);
    const apiHost = Constants.HOST_URL + "/api/";

    const fetchData = async () => {
      try {
        const response = await fetch(`${apiHost}service`);
        data.value = await response.json();
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };

    //onMounted(fetchData);

    return { services, data, fetchData };
  }
});
</script>

<style scoped>
</style>
