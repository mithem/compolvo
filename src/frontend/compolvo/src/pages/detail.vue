<template>
  <v-card class="card"  v-if="service != null">
    <!-- Service Image -->
    <v-img
      contain
      height="200"
      width="100%"
      aspect-ratio="16/9"
      :src="'/static/images/'+ service.system_name + '.png'"
      class="elevation-10"
    ></v-img>
    <!-- Service Name -->
    <v-card-title class="title">
      {{ service.name }}
    </v-card-title>
    <!-- Service Tags -->
    <div class="row">
      <div class="left-items">
        <span v-for="tag in service.tags" :key="tag.id" class="tag">{{ tag.label }}</span>
      </div>
      <div class="right-items">
        <span class="data-label">Downloads:</span> <span class="data-value">{{ service.download_count }}</span>
      </div>
    </div>

    <div class="row">
      <div class="left-items">
        <span v-for="os in formatedOs" key="formatedOs" class="tag">{{os}}</span>
      </div>
      <div class="right-items">
        <span class="data-label">License:</span> <span class="data-value">{{ formatedLicense }}</span>
      </div>
    </div>
    <!-- Description -->
    <v-card-text  class="desc">{{ service.description }}</v-card-text>






    <v-dialog max-width="750">
      <template v-slot:activator="{ props: activatorProps }">
        <v-btn
          v-bind="activatorProps"
          color="blue"
          prepend-icon="mdi-cart"
        >
          Order
        </v-btn>
      </template>
      <template v-slot:default="{ isActive }">
        <v-card class="pa-5">
          <v-col>
            <h1>New Order</h1>
            <h3>For {{ service.name }}</h3><br/>
            <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
            Subscription mode:
            <v-select
              v-if="service !== null"
              v-model="selectedOffering"
              label="Select offering"
              :items="selectableOfferings"
              item-title="price"
              item-value="id"
            ></v-select>
            <br/>

            <div v-if="selectedOffering !== null">
              {{ buyNowMsg }}
            </div>

            <v-card-actions>
              <v-spacer/>
              <v-btn
                text="Buy now"
                @click='createServicePlan(() => isActive.value=false)'
              ></v-btn>
            </v-card-actions>
          </v-col>
        </v-card>
      </template>
    </v-dialog>
    <v-snackbar
      v-model="showingSnackbar"
      color="success"
    >
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showingSnackbar=false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>

  </v-card>
  <v-progress-linear v-else color="blue" indeterminate :height="5">

  </v-progress-linear>


</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, onMounted, ref} from "vue";

import {DetailedService, License, OperatingSystem, ServiceOffering} from "../components/models";

interface SelectableOffering {
  props: { title: string, subtitle: string },
  id: string
}
export default defineComponent({
  setup() {
    const serviceId = ref("");
    const service = ref<DetailedService>(null)
    const loading = ref(false);
    const creating = ref(false);
    const selectedOffering = ref<string>(null);
    const selectableOfferings = ref<SelectableOffering[]>([]);
    const showingSnackbar = ref(false);
    const snackbarText = ref("");
    const buyNowMsg = ref("");
    const instance = getCurrentInstance().proxy
    const formatedLicense = ref<string>(null)
    const formatedOs = ref<string[]>(null)
    const licenses = ref<License[]>([])
    const oses = ref<OperatingSystem[]>([])

    const createServicePlan = async function (callback: () => void) {
      creating.value = true;
      try {
        const res = await fetch("/api/service/plan", {
          method: "POST",
          body: JSON.stringify({
            service_offering: selectedOffering.value
          })
        })
        if (!res.ok) {
          alert(await res.text())
        } else {
          callback();
          snackbarText.value = "Order successful."
          showingSnackbar.value = true;
        }
      } catch (err) {
        alert(err)
      }
      creating.value = false;
    }

    const fetchServiceData = async function () {
      loading.value = true;
      try {
        const res = await fetch("/api/service?id=" + instance.$route.query.id)
        if (!res.ok) {
          alert(await res.text())
        } else {
          service.value = JSON.parse(await res.text());
          selectableOfferings.value = service.value.offerings.map((offering: ServiceOffering) => {
            return {
              id: offering.id,
              props: {
                title: offering.name,
                subtitle: offering.price.toString()
              }
            }
          });
        }
        formatData()
      } catch (err) {
        alert(err)
      }
      loading.value = false;
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
    const formatData = () => {
        formatedOs.value = service.value.operating_systems.map(osId => {
          const foundOs = oses.value.find(os => os.id === osId)
          return foundOs ? foundOs.props.title : 'N/A'
        })
        const optLicense = licenses.value.filter(license => license.id == service.value.license)
        formatedLicense.value = optLicense.length > 0 ? optLicense[0].props.title : "N/A"
      }


    onMounted(async () => {
      await fetchLicenseOptions()
      await fetchOsOptions()
      await fetchServiceData()
    });

    return {
      licenses,
      oses,
      serviceId,
      service,
      loading,
      creating,
      selectableOfferings,
      selectedOffering,
      showingSnackbar,
      snackbarText,
      buyNowMsg,
      fetchServiceData,
      createServicePlan,
      formatedOs,
      formatedLicense
    };
  },
  watch: {
    selectedOffering(id: string) {
      const offering = this.service.offerings.find(offer => offer.id === id);
      if (offering != undefined) {
        this.buyNowMsg = "Buy now for " + offering.price.toString() + "€/" + offering.name + " (" + offering.duration_days + " days)?. The subscription will automatically renew."
      } else {
        this.buyNowMsg = "No offering selected."
      }
    },
  }
});
</script>

<style>

.card {
  width: 60%;
  margin: 0 auto;
  border-radius: 15px;
  padding: 20px;
}
.title {
  margin: 20px;
  padding: 20px;
  background-color: #333;
  color: white;
  text-align: center;
  font-size: 24px;
  font-weight: bold;
  border-radius: 5px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
.desc {
  padding: 15px;
  line-height: 1.6;
  font-size: 16px;
  color: #444;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin: 20px;
}
.card {
  width: 60%;
  margin: 0 auto;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  padding: 20px;
}

.tag {
  margin: 20px;
  padding: 3px 8px;
  background-color: #e1e1e1;
  border-radius: 4px;
  font-size: 0.9rem;
  display: inline-block;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px
}

.left-items {
  text-align: left;
}

.right-items {
  margin-right: 20px;
  text-align: right;
}

.data-label {
  font-weight: bold;
  color: #555;
}

.data-value {
  font-size: 16px;
  color: #000;
  font-weight: bold;
}

</style>
