<template>
  <v-card class="filter-card" title="Filter:">
    <v-list dense class="filter-list">
      <!-- Tags Filter with Custom Chips Display -->
      <v-list-item>
        <v-select
          v-model="filters.tags"
          :items="tagsOptions"
          label="Tags"
          multiple
          dense
        >
          <template v-slot:selection="{ item, index }">
            <v-chip v-if="index < 2" class="chip-custom">
              <span>{{ item.title }}</span>
            </v-chip>
            <span
              v-if="index === 2"
              class="text-grey text-caption align-self-center"
            >
              (+{{ filters.tags.length - 2 }} others)
            </span>
          </template>
        </v-select>
      </v-list-item>

      <!-- Price Range Filter with Label -->
      <v-list-item class="slider-list-item">
        <div class="label">Price:</div>
        <v-container>
          <v-range-slider
            v-model="filters.priceRange"
            :min="minPrice"
            :max="maxPrice"
            thumb-label="always"
            dense
            strict
            class="price-slider"
          />
        </v-container>
      </v-list-item>

      <!-- Owned Filter -->
      <v-list-item>
        <v-radio-group v-model="filters.owned" label="Owned" dense>
          <v-radio label="Yes" value="yes"></v-radio>
          <v-radio label="No" value="no"></v-radio>
        </v-radio-group>
      </v-list-item>

      <!-- License Filter -->
      <v-list-item>
        <v-select
          v-model="filters.license"
          :items="licenseOptions"
          label="License"
          dense
        ></v-select>
      </v-list-item>

      <!-- Operating System Filter -->
      <v-list-item>
        <v-select
          v-model="filters.os"
          :items="osOptions"
          label="OS"
          dense
        ></v-select>
      </v-list-item>

      <!-- Apply Filters Button -->
      <v-list-item>
        <v-btn block @click="applyFilters">Select</v-btn>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script lang="ts">
import {defineComponent} from 'vue';

interface Filters {
  tags: string[];
  priceRange: number[];
  owned: string;
  license: string;
  os: string;
}

export default defineComponent({
  data: () => ({
    filters: {
      tags: [],
      priceRange: [0, 100],
      owned: '',
      license: '',
      os: ''
    } as Filters,
    tagsOptions: ['foo', 'bar', 'fizz', 'buzz', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
    minPrice: 0,
    maxPrice: 100,
    licenseOptions: ['GPL', 'MIT', 'Apache'],
    osOptions: ['Windows', 'macOS', 'Linux']
  }),
  methods: {
    applyFilters(): void {
      console.log('Applied Filters:', this.filters);
    }
  }
});
</script>

<style scoped>
.filter-card {
  max-height: 100%;
}

.filter-list {
  margin-top: 20px;
}

.slider-list-item {
  margin-top: 24px;
}

.slider-list-item .label {
  font-size: 14px;
  color: rgba(0, 0, 0, .87);
  margin-bottom: 8px;
}

.price-slider .v-slider__thumb-label {
  background: white;
}

.chip-custom {
  color: #424242;
  background-color: #e0e0e0;
}
</style>
