<template>
  <filter_panel/>
  <!-- TODO:Delete Button when finished with testing-->
  <v-btn @click="fetchData">Load Data</v-btn>
  <!-- TODO:Center the div (the container) -->
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6" lg="4" v-for="service in services" :key="service.id">
        <compact-card
          :serviceName="service.name"
          :serviceVersion="service.latestVersion"
          :serviceDescription="service.description"
          :license="service.license"
          :serviceImage="service.image"
          :tags="service.tags"
          :downloadCount="service.download_count"
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
    // const services = ref([]);

    const apiHost = "http://localhost:8000/api/";
    const fetchData = async () => {
      try {
        const response = await fetch(`${apiHost}service`);
        if (response.ok) {
          const jsonData = await response.json();
          services.value = jsonData.map(service => ({
            id: service.id,
            name: service.name,
            description: service.description,
            license: service.license,
            download_count: service.download_count,
            tags: service.tags,
            image: service.image || 'https://cdn.vuetifyjs.com/images/cards/sunshine.jpg', // Default image if none is provided
            latestVersion: service.latest_version || 'N/A', // Updated to use latest_version and provide default if absent
            price: formatPriceWithDuration(service.offerings)  // Format price with duration
          }));
          console.log(jsonData);  // Debugging line to see what's fetched
        } else {
          throw new Error('Failed to fetch');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };

    const formatPriceWithDuration = (offerings) => {
      if (offerings && offerings.length > 0) {
        const offering = offerings[0]; // Assuming we're only interested in the first offering
        return `$${offering.price.toFixed(2)} / ${offering.name}`; // Formats the price with duration
      }
      return 'Free';  // Default to 'Free' if no offerings
    };

    onMounted(fetchData);

    return { services, fetchData };
  }
});
</script>

<style scoped>
</style>
