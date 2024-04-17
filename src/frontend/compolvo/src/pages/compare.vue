<template>
  <v-container fluid>
    <v-row style="margin: 0">
      <filter_panel @applyFilter="filterServices($event)" style="flex-grow: 1"/>
      <v-container style="flex-grow: 3; margin:0; padding-top: 0">
        <v-row>
          <v-col cols="12" md="6" lg="4" v-for="service in filteredServices" :key="service.id">
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
    </v-row>
  </v-container>
</template>

<script lang="ts">
import {defineComponent, ref, onMounted} from 'vue';
import CompactCard from '@/components/compact_card.vue'; // Adjust the path as necessary
import Constants from "../components/Constants"; // Adjust the path as necessary

export default defineComponent({
  components: {
    CompactCard
  },
  setup() {
    const services = ref([]);
    const filteredServices = ref([]);

    const apiHost = Constants.HOST_URL + "/api/";
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
          await filterServices(null)
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
      return 'N/A';
    };

    onMounted(fetchData);

    const filterServices = async function (filter) {
      let result = services.value;
      if (filter) {
        if (filter.tags.length > 0) {
          result = result.filter(service => filter.tags.some(tag => service.tags.includes(tag)));
        }
        result = result.filter(service => {
          const priceNumber = parseFloat(service.price.replace(/[^0-9\.]+/g, ""));
          return priceNumber >= filter.priceRange[0] && priceNumber <= filter.priceRange[1];
        });
        if (filter.owned !== '') {
          result = result.filter(service => service.owned === filter.owned);
        }
        if (filter.license !== '') {
          result = result.filter(service => service.license === filter.license);
        }
        if (filter.os !== '') {
          result = result.filter(service => service.os && service.os.includes(filter.os));
        }
        console.log(result)
      }
      filteredServices.value = result
      console.log(filter);
    }

    return {services, filteredServices, fetchData, filterServices};
  }
});
</script>

<style scoped>
</style>
