<template>
  <v-container fluid>
    <v-row style="margin: 0">
      <filter_panel @applyFilter="filterServices($event)" style="flex-grow: 1"/>
      <v-container style="flex-grow: 3; margin:0; padding-top: 0; max-width: 80%">
        <v-row>
          <v-col cols="12" md="6" lg="4" v-for="service in filteredServices" :key="service.service.id">
            <compact-card
              :filteredService=service
              :targetDurationDays=targetDurationDays
            />
          </v-col>
        </v-row>
      </v-container>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import {defineComponent, ref, onMounted, getCurrentInstance} from 'vue';
import CompactCard from '@/components/compact_card.vue';
import Constants from "../components/Constants";
import {DetailedService, ServiceOffering} from '../components/models';
import {Filters} from '../components/filter_panel.vue';

export interface FilteredService {
  service: DetailedService;
  calculatedPrice: number;
  selectedOffering: ServiceOffering;
}

export default defineComponent({
  components: {
    CompactCard
  },
  setup() {
    const instance = getCurrentInstance()
    const services = ref<DetailedService[]>([]);
    const filteredServices = ref<FilteredService[]>([]);
    const targetDurationDays = ref(30)

    const apiHost = Constants.HOST_URL + "/api/";
    const fetchData = async () => {
      try {
        const response = await fetch(`${apiHost}service`);
        if (response.ok) {
          services.value = await response.json();
          console.log(services.value);  // Debugging line to see what's fetched
          await filterServices(null)
        } else {
          throw new Error('Failed to fetch');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    }

    onMounted(fetchData);

    const filterServices = async function (filter: Filters) {
      if (filter != null) {
        switch (filter.period) {
          case 0:
            targetDurationDays.value = 1;
            break;
          case 1:
            targetDurationDays.value = 30;
            break;
          case 2:
            targetDurationDays.value = 360;
            break;
        }
        console.log("Knechter")
        console.log(targetDurationDays.value)
      }
      filteredServices.value = services.value.map((service: DetailedService) => {
        const priceForService = getPriceForService(service.offerings);
        return {
          service: service,
          calculatedPrice: priceForService[0] as number,
          selectedOffering: priceForService[1] as ServiceOffering,
        }
      })
      let result = filteredServices.value;
      if (filter) {
        if (filter.tags.length > 0) {
          result = result.filter(service => filter.tags.every(tag => service.service.tags.filter((svcTag) => {
            return tag.id === svcTag.id;
          }).length > 0));
        }
        result = result.filter(service => {
          return service.calculatedPrice >= filter.priceRange[0] && service.calculatedPrice <= filter.priceRange[1];
        });
        if (filter.license !== '') {
          result = result.filter(service => service.service.license === filter.license);
        }
        if (filter.os !== '') {
          /* Kommt noch trust */
          result = result.filter(service => service.service.os && service.service.os.includes(filter.os));
        }
      }
      filteredServices.value = result
      console.log("Knecht");
      console.log(filteredServices);
      console.log(filter);
      /* instance.proxy.$forceUpdate() */
      /* TODO: add reload after pressing the select button  */
    }

    const getPriceForService = (offerings: ServiceOffering[]) => {
      const filtered = offerings.filter((offering: ServiceOffering) => {
        return offering.duration_days === targetDurationDays.value
      }).sort((a, b) => {
        if (a.price < b.price) {
          return -1
        }
        if (a.price > b.price) {
          return 1
        }
        return 0;
      })
      if (filtered.length > 0) {
        return [offerings[0].price, offerings[0]]
      }
      const offering = offerings.sort((a, b) => {
        if (a.duration_days > b.duration_days) {
          return -1
        }
        if (a.duration_days < b.duration_days) {
          return 1
        }
        return 0;
      })[0]
      return [targetDurationDays.value / offering.duration_days * offering.price, offering]
    }

    return {services, filteredServices, targetDurationDays, fetchData, filterServices, getPriceForService};
  }
});
</script>

<style scoped>
</style>
