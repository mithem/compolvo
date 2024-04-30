<template>
  <filter_panel @applyFilter="filterServices($event)" style="flex: 1; box-sizing: border-box" :licenses=licenses
                :oses="oses"/>
  <v-container class="cardsContainer">
      <v-col cols="4" v-for="service in filteredServices" :key="service.service.id">
        <compact-card
          :filteredService=service
          :targetDurationDays=targetDurationDays
          :licenses=licenses
          :oses=oses
        />
      </v-col>
  </v-container>
</template>

<script lang="ts">
import {defineComponent, ref, onMounted, getCurrentInstance} from 'vue';
import CompactCard from '@/components/compact_card.vue';
import Constants from "../components/Constants";
import {DetailedService, License, OperatingSystem, ServiceOffering} from '../components/models';
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
    const licenses = ref<License[]>([])
    const oses = ref<OperatingSystem[]>([])

    const apiHost = Constants.HOST_URL + "/api/";
    const fetchData = async () => {
      try {
        const response = await fetch(`${apiHost}service`);
        if (response.ok) {
          services.value = await response.json()
          console.log("Services Maped", services.value);  // Debugging line to see what's fetched
          await filterServices(null)
        } else {
          throw new Error('Failed to fetch');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    }

    const fetchOsOptions = async () => {
      try {
        const response = await fetch(`/api/operating-system`);
        if (response.ok) {
          oses.value = (await response.json()).map((os) => {
            return {props: {title: os.name}, id: os.id}
          });
          console.log("oses", oses.value);  // Debugging line to see what's fetched
        } else {
          throw new Error('Failed to fetch');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    }
    const fetchLicenseOptions = async () => {
      try {
        const response = await fetch(`/api/license`);
        if (response.ok) {
          licenses.value = (await response.json()).map((license) => {
            return {props: {title: license.name}, id: license.id}
          });
          console.log("licenses", licenses.value);  // Debugging line to see what's fetched
        } else {
          throw new Error('Failed to fetch');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    }

    onMounted(async () => {
      await fetchLicenseOptions()
      await fetchOsOptions()
      await fetchData()
    });

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
      }
      filteredServices.value = services.value.map((service: DetailedService) => {
        const priceForService = getPriceForService(service.offerings);
        console.log("priceForService", priceForService)
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
        if (filter.license !== null) {
          result = result.filter(service => service.service.license === filter.license.id);
        }
        if (filter.os !== null) {
          result = result.filter(service => service.service.operating_systems.some(os => (os === filter.os.id)));
        }
      }
      // ensures that the cards are getting reloaded if the period is changed in the filter
      filteredServices.value = []
      setTimeout(() => {
        filteredServices.value = result
      }, 0)
    }

    const getPriceForService = (offerings: ServiceOffering[]) => {
      const filtered = offerings.filter((offering: ServiceOffering) => {
        console.log(offering.service)
        console.log("offering.duration_days", offering.duration_days)
        console.log("targetDurationDays.value", targetDurationDays.value)
        console.log("---------------------------------------------------")
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
      console.log("filtered", filtered)
      if (filtered.length > 0) {
        return [filtered[0].price, filtered[0]]
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

    return {
      services,
      filteredServices,
      targetDurationDays,
      fetchData,
      filterServices,
      getPriceForService,
      licenses,
      oses
    };
  }
});
</script>

<style scoped>
.cardsContainer {
  flex: 3;
  box-sizing: border-box;
  flex-wrap: wrap;
  display: flex;
  overflow: hidden;
  overflow-y: scroll;
  margin: 0;
  padding-top: 0;
  height: 90vh;
}
</style>
