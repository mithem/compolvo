<template>
  <v-card class="card" v-if="service != null">
    <!-- Service Image -->
    <!-- Service Image -->
    <v-img
      contain
      height="200"
      width="100%"
      aspect-ratio="16/9"
      :src="'/static/images/'+ service.system_name + '.png'"
    ></v-img>

    <!-- Service Name -->
    <v-card-title class="title">
      {{ service.name }}
    </v-card-title>

    <!-- Combined Row for Tags, Button, and Downloads -->
    <div class="combined-row">
      <div class="tag-container">
        <span v-for="tag in service.tags" :key="tag.id" class="tag">{{ tag.label }}</span>
      </div>

      <!-- Scroll Down Button -->
      <div class="button-container" v-if="canScroll">
        <v-btn @click="scrollToBottom" variant="text" color="secondary">
          <v-icon>
            mdi-chevron-double-down
          </v-icon>
        </v-btn>
      </div>

      <div class="download-container">
        <span class="data-label">Downloads:</span>
        <span class="data-value">{{ service.download_count || "N/A" }}</span>
      </div>
    </div>


    <!-- Operating Systems -->
    <div class="row">
      <div class="left-items">
        <span v-for="os in formatedOs" key="formatedOs" class="tag">{{ os }}</span>
      </div>
      <!-- License -->
      <div class="right-items">
        <span class="data-label">License:</span> <span class="data-value">{{
          formatedLicense
        }}</span>
      </div>
    </div>
    <!-- Description -->
    <div class="desc" v-html=compileMarkdownDescription()></div>
    <div v-if="service.offerings.length > 0">
      <hr/>
      <div class="slide-group-container">
        <v-icon
          class="slide-group-hint"
          @click="scrollOfferings(false)"
        >mdi-chevron-left
        </v-icon>
        <div class="offering-slide-group" id="service-offering-slide-group">
          <div
            v-for="offering in service.offerings"
          >
            <ServiceOfferingCard :offering=offering></ServiceOfferingCard>
          </div>
        </div>
        <v-icon
          class="slide-group-hint"
          @click="scrollOfferings(true)"
        >mdi-chevron-right
        </v-icon>
      </div>
    </div>
  </v-card>
  <v-progress-linear v-else indeterminate>
  </v-progress-linear>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, onMounted, onUnmounted, ref} from "vue";
import {DetailedService, License, OperatingSystem, ServiceOffering} from "../components/models";
import {marked} from "marked";
import ServiceOfferingCard from "../components/ServiceOfferingCard.vue";

interface SelectableOffering {
  props: { title: string, subtitle: string },
  id: string
}

export default defineComponent({
  components: {ServiceOfferingCard},
  setup() {
    const serviceId = ref("");
    const service = ref<DetailedService>(null)
    const loading = ref(false);
    const selectedOffering = ref<string>(null);
    const selectableOfferings = ref<SelectableOffering[]>([]);
    const buyNowMsg = ref("");
    const instance = getCurrentInstance().proxy
    const formatedLicense = ref<string>(null)
    const formatedOs = ref<string[]>(null)
    const licenses = ref<License[]>([])
    const oses = ref<OperatingSystem[]>([])
    const canScroll = ref(false);

    const checkScroll = () => {
      const body = document.body;
      const html = document.documentElement;
      const docHeight = Math.max(body.scrollHeight, body.offsetHeight,
        html.clientHeight, html.scrollHeight, html.offsetHeight);
      const windowHeight = window.innerHeight;
      canScroll.value = docHeight > windowHeight;
    };

    const compileMarkdownDescription = () => {
      return service.value.description !== null ? marked(service.value.description) : "No description."
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

    const scrollToBottom = () => {
      window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
      });
    }

    const scrollOfferings = (direction: boolean) => {
      const multiplicator = direction ? 1 : -1
      document.getElementById("service-offering-slide-group").scrollBy({
        left: multiplicator * 200,
        behavior: "smooth"
      })
    }

    onMounted(async () => {
      await fetchLicenseOptions()
      await fetchOsOptions()
      await fetchServiceData()
      window.addEventListener('resize', checkScroll);
      checkScroll();
    });

    onUnmounted(() => {
      window.removeEventListener('resize', checkScroll);
    });

    return {
      compileMarkdownDescription,
      licenses,
      oses,
      serviceId,
      service,
      loading,
      selectableOfferings,
      selectedOffering,
      buyNowMsg,
      fetchServiceData,
      formatedOs,
      formatedLicense,
      scrollToBottom,
      scrollOfferings,
      canScroll
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
  background-color: rgb(var(--v-theme-text-background-secondary));
  border-radius: 8px;
  margin: 20px;
}

.card {
  width: 60%;
  margin: 0 auto;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  padding: 20px;
}

.tag {
  padding: 3px 8px;
  background-color: rgb(var(--v-theme-background-secondary));
  border-radius: 4px;
  font-size: 0.9rem;
  display: inline-block;
}

.row {
  display: flex;
  justify-content: space-between;
  position: relative;
  z-index: 0;
  align-items: center;
  margin: 10px 20px;
}

.left-items {
  text-align: left;
  display: flex;
  gap: 20px;
}

.right-items {
  margin-right: 20px;
  text-align: right;
}

.data-label {
  font-weight: bold;
  color: rgb(var(--v-theme-text-secondary));
}

.data-value {
  font-size: 16px;

  font-weight: bold;
}

.slide-group-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.offering-slide-group {
  padding: 10px;
  border-radius: 10px;
  display: flex;
  overflow-x: auto;
  scrollbar-width: none;
  gap: 15px;
}

.offering-slide-group::-webkit-scrollbar {
  display: none;
  width: 0;
  background: transparent;
}

.slide-group-hint {
  animation: blinker 1s linear infinite;
}

@keyframes blinker {
  50% {
    opacity: 50%;
  }
}

.button-container {
  flex-grow: 0;
  margin: 0 20px; /* Adjust margin to ensure it does not stretch */
}

.combined-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10px 20px;
}

.download-container {
  flex: 1;
  text-align: right;
}

.tag-container {
  flex: 1;
  text-align: left;
  display: flex;
  gap: 20px;
}
</style>
