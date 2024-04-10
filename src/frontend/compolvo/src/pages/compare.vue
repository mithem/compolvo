<template>
  <v-card class="service-card">
    <!-- Service Name -->
    <!--TODO:use v-row and v-column for the design -->
    <v-card-title>{{ serviceName }}</v-card-title>

    <!-- Service Version -->
    <v-card-subtitle class="version">{{ serviceVersion }}</v-card-subtitle>

    <!-- Service Description -->
    <v-card-text>{{ serviceDescription }}</v-card-text>

    <!-- License -->
    <v-card-text>License: {{ license }}</v-card-text>

    <!-- Tags -->
    <v-card-text>
      <div class="tags">
        <span v-for="(tag, index) in tags" :key="index" class="tag">{{ tag }}</span>
      </div>
    </v-card-text>

    <!-- Download Count and Price -->
    <v-card-actions class="bottom-right">
      <div>Downloads: {{ downloadCount }}</div>
      <div>Price: {{ price }}</div>
    </v-card-actions>
  </v-card>
</template>

<script setup>
const serviceName = "Service Name";
const serviceVersion = "1.0.0";
const serviceDescription = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer dignissim, nisi id fermentum lacinia, sapien turpis tristique est, id tincidunt metus eros vel leo.";
const license = "MIT";
const tags = ["Tag1", "Tag2", "Tag3"];
const downloadCount = 1000;
const price = "$9.99"; // Set to null or another appropriate value if it's a free service
</script>

<style scoped>
.service-card {
  width: 400px;
}

.version {
  text-align: right;
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
