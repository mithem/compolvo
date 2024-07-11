compact_card.vue
<template>
  <v-card :to="{path: 'detail', query:{id: filteredService.service.id} }" class="compact-card">
    <v-card-title>
          <v-img
            contain
            height="200"
            aspect-ratio="16/9"
            :src="'/static/images/' + filteredService.service.system_name + '.png'"
          ></v-img>
          {{ filteredService.service.name }}
    </v-card-title>

    <!-- Service Description -->
    <v-card-text class="desc">{{ filteredService.service.short_description }}</v-card-text>

    <!-- License -->
    <v-card-text>License: {{ formatedLicense }}</v-card-text>

    <!-- Os -->
    <v-card-text>
      <div class="tags">
        <span v-for="os in formatedOs" key="formatedOs" class="tag">{{os}}</span>
      </div>
    </v-card-text>

    <!-- Tags -->
    <v-card-text>
      <div class="tags">
        <span v-for="tag in filteredService.service.tags" key="tag.id" class="tag">{{ tag.label }}</span>
      </div>
    </v-card-text>

    <!-- Download Count and Price -->
    <v-card-actions class="bottom-right">
      <div>Downloads: {{ filteredService.service.download_count !== null ? formatLargeNumber(filteredService.service.download_count) : "N/A"}}</div>
      <div>Price: {{formatPriceMean(filteredService.calculatedPrice,filteredService.selectedOffering)}}</div>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import {defineComponent, ref} from 'vue';
import {FilteredService} from '../pages/compare.vue';
import {License, OperatingSystem} from "./models";
import {formatLargeNumber} from "./utils";

export default defineComponent({
  name: 'CompactCard',
  methods: {formatLargeNumber},
  props: ["filteredService", "targetDurationDays", "licenses", "oses"],
  setup(
    props: {
      filteredService: FilteredService,
      targetDurationDays: number
      licenses: License[]
      oses: OperatingSystem[]
    }) {
    const filteredService = ref<FilteredService>(props.filteredService);
    const targetDurationDays = ref(props.targetDurationDays)
    const formatedLicense = ref<string>(null)
    const formatedOs = ref<string[]>(null)

    console.log("cards",filteredService)


    formatedOs.value = filteredService.value.service.operating_systems.map(osId => {
      const foundOs = props.oses.find(os => os.id === osId)
      return foundOs ? foundOs.props.title : 'N/A'
    })

    const optLicense = props.licenses.filter(license => license.id == filteredService.value.service.license)
    formatedLicense.value = optLicense.length > 0 ? optLicense[0].props.title : "N/A"


    const formatPriceMean = (calcPrice,offering) => {
      if (offering === null) {
        return "N/A"
      }
      let periodName = "";
      switch (targetDurationDays.value) {
        case 1: periodName = "day"; break
        case 30: periodName = "month"; break
        case 360: periodName = "year"; break
      }
      return `$${calcPrice.toFixed(2)} / ${periodName} (paid each ${offering.name})`;
    }

    return {
      filteredService,
      formatPriceMean,
      formatedLicense,
      formatedOs
    };
  }
});
</script>

<style scoped>
.compact-card {
  flex-direction: column;
  border-radius: 5px;
}

.version {
  text-align: right;
}

.desc {
  height: 100px;
  overflow: auto;
  padding: 15px;
  line-height: 1.6;
  font-size: 16px;
  background-color: rgb(var(--v-theme-text-background-secondary));
  border-radius: 8px;
  margin: 20px;
}

.tags .tag {
  margin-right: 5px;
  padding: 3px 8px;
  background-color: rgb(var(--v-theme-background-secondary));
  border-radius: 4px;
  font-size: 12px;
}

.bottom-right {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
}
</style>
