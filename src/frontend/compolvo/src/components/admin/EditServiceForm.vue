<template>
  <v-form>
    <v-col>
      <v-row class="vert-input-field">
        <v-switch
          inline
          class="horiz-input-field"
          v-model="service.hidden"
          label="Hidden"
        ></v-switch>
        <v-text-field
          class="horiz-input-field"
          v-model="service.system_name"
          label="System name"
          mandatory
        ></v-text-field>
        <v-text-field
          class="horiz-input-field"
          v-model="service.name"
          label="Name"
          mandatory
        ></v-text-field>
      </v-row>
      <v-text-field
        v-model="service.short_description"
        label="Short description"
      ></v-text-field>
      <v-textarea
        v-model="service.description"
        label="Description"
      ></v-textarea>
      <v-row class="vert-input-field">
        <v-text-field
          v-model="service.download_count"
          class="horiz-input-field"
          label="Download count"
        ></v-text-field>
        <v-select
          v-model="selectedLicense"
          :items="mappedLicenses"
          class="horiz-input-field"
          label="License"
          mandatory
        >
        </v-select>
      </v-row>
      <v-select
        v-model="selectedTags"
        :items="mappedTags"
        label="Tags"
        multiple
      ></v-select>
      <v-row>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          text="Save"
          @click="save"
        ></v-btn>
      </v-row>
    </v-col>
  </v-form>
</template>

<script lang="ts">
import {defineComponent, getCurrentInstance, ref} from 'vue';
import {License, SelectableListEntry, Tag} from "../models";

export interface OptionalService {
  hidden: boolean
  name: string,
  system_name: string,
  short_description: string | null,
  description: string | null,
  download_count: number,
  license: string | null,
  tags: Tag[]
}

export default defineComponent({
  name: 'EditServiceForm',
  props: ["licenses", "service", "tags"],
  setup(props: {
    licenses: License[],
    service: OptionalService | null,
    tags: Tag[]
  }) {
    const error = ref<Error | null>(null)
    const selectedLicense = ref<SelectableListEntry | null>(null)
    const licenses = props.licenses
    const mappedLicenses = licenses.map(l => {
      return {id: l.id, props: {title: l.name, subtitle: l.id}}
    })
    const mappedTags = props.tags.map(t => {
      return {id: t.id, props: {title: t.label, subtitle: t.id}}
    })
    const serviceTags = props.service === null ? [] : props.service.tags.map(t => t.id)
    const startTagSelection = mappedTags.filter(tag => serviceTags.includes(tag.id))
    const selectedTags = ref<SelectableListEntry[]>(startTagSelection)
    const instance = getCurrentInstance()
    const service = ref<OptionalService>({
      hidden: false,
      name: "",
      system_name: "",
      short_description: "",
      description: "",
      download_count: 0,
      license: null,
      tags: []
    })
    if (props.service !== null) {
      service.value = props.service
      selectedLicense.value = mappedLicenses.filter(l => l.id === service.value.license)[0]
    }

    const save = async function () {
      service.value.license = selectedLicense.value.id
      service.value.tags = selectedTags.value.map(t => {
        return {id: t.id, label: t.props.title}
      })
      instance.proxy.$emit("service-save", service.value)
    }

    return {
      error,
      licenses,
      mappedLicenses,
      selectedLicense,
      mappedTags,
      selectedTags,
      service,
      save
    }
  },
})
</script>

<style scoped>

</style>
