compact_card.vue
<template>
  <v-card class="compact-card">
    <v-card-title>
      <v-row no-gutters>
        <v-col cols="12">
          <v-img
            height="200"
            aspect-ratio="16/9"
            cover
            :src="filteredService.service.image"
          ></v-img>
        </v-col>
        <v-col cols="12" class="py-2 text-h6">
          {{ filteredService.service.name }}
        </v-col>
      </v-row>
    </v-card-title>

    <!-- Service Version -->
    <v-card-subtitle class="version">{{ filteredService.service.latest_version }}</v-card-subtitle>

    <!-- Service Description -->
    <v-card-text class="desc">{{ filteredService.service.description }}</v-card-text>

    <!-- License -->
    <v-card-text>License: {{ filteredService.service.license }}</v-card-text>

    <!-- Tags -->
    <v-card-text>
      <div class="tags">
        <span v-for="tag in filteredService.service.tags" key="tag.id" class="tag">{{ tag.label }}</span>
      </div>
    </v-card-text>

    <!-- Download Count and Price -->
    <v-card-actions class="bottom-right">
      <div>Downloads: {{ filteredService.service.download_count }}</div>
      <div>Price: {{formatPriceMean(filteredService.calculatedPrice,filteredService.selectedOffering)}}</div>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import {defineComponent, ref} from 'vue';
import { FilteredService } from '../pages/compare.vue';

export default defineComponent({
  name: 'CompactCard',
  props:["filteredService","targetDurationDays"],
  setup(
    props: {
      filteredService: FilteredService,
      targetDurationDays: number
    }) {
    const filteredService = ref<FilteredService>(props.filteredService);
    const targetDurationDays = ref(props.targetDurationDays)

    const formatPriceMean = (calcPrice,offering) => {
      let periodName = "";
      switch (targetDurationDays.value) {
        case 1: periodName = "day"; break
        case 30: periodName = "month"; break
        case 360: periodName = "year"; break
      }
      return `$${calcPrice.toFixed(2)} / ${periodName} (paid each ${offering.name})`;
    }
    console.log("Oberknecht")
    console.log(filteredService)
    console.log(targetDurationDays)

    return {
      filteredService,
      formatPriceMean
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
