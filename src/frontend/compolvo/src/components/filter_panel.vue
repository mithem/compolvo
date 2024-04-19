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
          clearable
          key="id"
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


      <v-container class="slider-list-item">
        <div class="label">Period:</div>
        <v-slider
          v-model="filters.period"
          :max="2"
          :ticks="periodOptions"
          show-ticks="always"
          step="1"
          tick-size="4"
        ></v-slider>
      </v-container>

      <!-- License Filter -->
      <v-list-item>
        <v-select
          v-model="filters.license"
          :items="licenseOptions"
          label="License"
          dense
          clearable
        ></v-select>
      </v-list-item>

      <!-- Operating System Filter -->
      <v-list-item>
        <v-select
          v-model="filters.os"
          :items="osOptions"
          label="OS"
          dense
          clearable
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
import {Tag} from "./models";

export interface Filters {
  tags: Tag[];
  priceRange: number[];
  license: string;
  os: string;
  period: number;
}
export default defineComponent({
  //TODO add duration filter
  data: () => ({
    filters: {
      tags: [],
      priceRange: [0, 10000],
      license: '',
      os: '',
      period: 1
    } as Filters,
    tagsOptions: [
      {id: "f9040a1d-d539-4c22-b2dc-b86c7c0ec085", label: "Developer", props: {title: "Developer"}},
      {id: "98d664b5-b5a2-4fe8-bd81-f63023e916a5", label: "Enthusiast", props: {title: "Enthusiast"}},
    ],
    periodOptions: {
      0: "Day",
      1: "Month",
      2: "Year",
    },
    minPrice: 0,
    maxPrice: 10000,
    licenseOptions: ['GPL', 'MIT', 'Apache'],
    osOptions: ['Windows', 'macOS', 'Linux']
  }),
  methods: {
    applyFilters(): void {
      console.log('Applied Filters:', this.filters);
      this.$emit('applyFilter', this.filters)
    }
  }
});
</script>

<style scoped>
.filter-card {
  max-height: 100%;
  max-width: 20%;
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
