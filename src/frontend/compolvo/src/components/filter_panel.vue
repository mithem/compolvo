<template>
  <v-card class="filter-card" title="Filter:">
    <v-list dense class="filter-list">
      <!-- Tags Filter with Custom Chips Display -->
      <v-list-item class="filter-list-item">
        <v-select
          v-model="filters.tags"
          :items="tags"
          label="Tags"
          multiple
          dense
          clearable
          key="id"
        >
          <template v-slot:selection="{ item, index }">
            <v-chip v-if="index < 2" class="chip-custom">
              <span>{{ item.value.props.title }}</span>
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
      <v-list-item class="slider-list-item, filter-list-item">
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

      <!-- Period Filter -->
      <v-container class="slider-list-item, filter-list-item">
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
      <v-list-item class="filter-list-item">
        <v-select
          v-model="filters.license"
          :items="licenses"
          label="License"
          dense
          clearable
        ></v-select>
      </v-list-item>

      <!-- Operating System Filter -->
      <v-list-item class="filter-list-item">
        <v-select
          v-model="filters.os"
          :items="oses"
          label="OS"
          dense
          clearable
        ></v-select>
      </v-list-item>

      <!-- Apply Filters Button -->
      <v-list-item class="filter-list-item">
        <v-btn block @click="applyFilters">Select</v-btn>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script lang="ts">
import {defineComponent, onMounted, ref} from 'vue';
import {License, OperatingSystem, Tag} from "./models";


export interface Filters {
  tags: Tag[];
  priceRange: number[];
  license: License | null;
  os: OperatingSystem | null;
  period: number;
}

export default defineComponent({
  name: 'Filter',
  props: ['licenses', 'oses'],
  setup(
    props: {
      licenses: License[]
      oses: OperatingSystem[]
    }) {
    const tags = ref<Tag[]>([])

    const fetchTagOptions = async () => {
      try {
        const response = await fetch(`/api/tag`);
        if (response.ok) {
          tags.value = (await response.json()).map((tag) => {
            return {props: {title: tag.label}, id: tag.id}
          });
          console.log(tags.value);  // Debugging line to see what's fetched
        } else {
          throw new Error('Failed to fetch');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    }

    onMounted(fetchTagOptions)


    return {fetchTagOptions, tags};
  },

  data: () => ({
    filters: {
      tags: [],
      priceRange: [0, 10000],
      license: null,
      os: null,
      period: 1
    } as Filters,
    periodOptions: {
      0: "Day",
      1: "Month",
      2: "Year",
    },
    minPrice: 0,
    maxPrice: 1000,
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
  overflow: auto;
}

.filter-list {
  margin-top: 10px;
}

.filter-list-item {
  flex: 1;
}

.slider-list-item .label {
  font-size: 14px;
  color: rgba(0, 0, 0, .87);
}

.price-slider .v-slider__thumb-label {
  background: white;
}

.chip-custom {
  color: #424242;
  background-color: #e0e0e0;
}
</style>
