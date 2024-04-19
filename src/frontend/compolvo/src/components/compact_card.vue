<template>
  <v-card class="compact-card">
    <v-card-title>
      <v-row no-gutters>
        <v-col cols="12">
          <v-img
            height="200"
            aspect-ratio="16/9"
            cover
            :src="detailedService.image"
          ></v-img>
        </v-col>
        <v-col cols="12" class="py-2 text-h6">
          {{ detailedService.name }}
        </v-col>
      </v-row>
    </v-card-title>

    <!-- Service Version -->
    <v-card-subtitle class="version">{{ detailedService.latest_version }}</v-card-subtitle>

    <!-- Service Description -->
    <v-card-text class="desc">{{ detailedService.description }}</v-card-text>

    <!-- License -->
    <v-card-text>License: {{ detailedService.license }}</v-card-text>

    <!-- Tags -->
    <v-card-text>
      <div class="tags">
        <span v-for="tag in detailedService.tags" key="id" class="tag">{{ tag.label }}</span>
      </div>
    </v-card-text>

    <!-- Download Count and Price -->
    <v-card-actions class="bottom-right">
      <div>Downloads: {{ detailedService.download_count }}</div>
      <div>Price: {{ getPriceForService(detailedService.offerings) }}</div>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import {defineComponent, ref} from 'vue';
import {DetailedService, ServiceOffering} from "./models";

export default defineComponent({
  name: 'CompactCard',
  setup(
    props: {
      detailedService: DetailedService
      targetDurationDays: number
    }) {

    const targetDurationDays = ref(props.targetDurationDays)

    const getPriceForService = (offerings: ServiceOffering[]) => {
      const filtered = offerings.filter((offering: ServiceOffering) => {
        return offering.duration_days === props.targetDurationDays
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
        return formatPriceWithDuration(offerings[0])
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
      return (targetDurationDays.value / offering.duration_days * offering.price).toString()
      //TODO: add formating for offering without specified duration (mean of price for selected day range)
    }


    const formatPriceWithDuration = (offering) => {
      return `$${offering.price.toFixed(2)} / ${offering.name}`;
    }

    return {
      formatPriceWithDuration,
      getPriceForService,
      targetDurationDays
    };
  }
});
</script>

<style scoped>
.compact-card {
  min-width: auto;
  max-width: 100%;
  max-height: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.version {
  text-align: right;
}

.desc {
  max-height: 100px;
  overflow: auto;
}

.tags .tag {
  margin-right: 5px;
  padding: 3px 8px;
  background-color: #ddd;
  border-radius: 4px;
  font-size: 12px;
}

.bottom-right {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
}
</style>
