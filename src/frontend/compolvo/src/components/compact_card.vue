<template>
  <v-card class="compact-card">
    <v-card-title>
      <v-row no-gutters>
        <v-col cols="12">
          <v-img
            height="200"
            aspect-ratio="16/9"
            cover
            :src="serviceImage"
          ></v-img>
        </v-col>
        <v-col cols="12" class="py-2 text-h6">
          {{ serviceName }}
        </v-col>
      </v-row>
    </v-card-title>

    <!-- Service Version -->
    <v-card-subtitle class="version">{{ serviceVersion }}</v-card-subtitle>

    <!-- Service Description -->
    <v-card-text class="desc">{{ serviceDescription }}</v-card-text>

    <!-- License -->
    <v-card-text>License: {{ license }}</v-card-text>

    <!-- Tags -->
    <v-card-text>
      <div class="tags">
        <span v-for="tag in tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </v-card-text>

    <!-- Download Count and Price -->
    <v-card-actions class="bottom-right">
      <div>Downloads: {{ downloadCount }}</div>
      <div>Price: {{ price }}</div>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import {defineComponent} from 'vue';

export default defineComponent({
  name: 'CompactCard',
  props: {
    serviceImage: String,
    serviceName: String,
    serviceVersion: String,
    serviceDescription: String,
    license: String,
    tags: {
      type: Array as () => string[],
      default: () => []
    },
    downloadCount: Number,
    price: Number,
  }
})
</script>

<style scoped>
.compact-card {
  max-width: 400px;
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
