<template>
  <v-card class="card">
    <v-img
      v-if="service != null"
      contain
      height="200"
      width="100%"
      aspect-ratio="16/9"
      :src="'/static/images/'+ service.system_name + '.png'"
      style="box-shadow: 10px 10px 1rem #555 "
    ></v-img>


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


</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, onMounted, ref} from "vue";

import {ServiceOffering} from "../components/models";

interface SelectableOffering {
  props: { title: string, subtitle: string },
  id: string
}
export default defineComponent({
  setup() {
    const serviceId = ref("");
    const service = ref<Service>(null)
    const loading = ref(false);
    const creating = ref(false);
    const selectedOffering = ref<string>(null);
    const selectableOfferings = ref<SelectableOffering[]>([]);
    const showingSnackbar = ref(false);
    const snackbarText = ref("");
    const buyNowMsg = ref("");
    const instance = getCurrentInstance().proxy

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
      } catch (err) {
        alert(err)
      }
      loading.value = false;
    }

    onMounted(fetchServiceData);

    return {
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
      createServicePlan
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
    }
  }
});
</script>

<style>

.card {
  width: 60%;
  margin: 0 auto;
  border-radius: 15px;
}

</style>
