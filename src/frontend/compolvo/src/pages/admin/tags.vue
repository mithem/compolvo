<template>
  <v-col>
    <ErrorPanel :error="error"></ErrorPanel>
    <v-data-table
      v-model="selectedTags"
      :headers="headers"
      :items="tags"
      item-key="id"
      show-select
      class="elevation-1"
      :loading="loading"
    >
      <template v-slot:top>
        <v-toolbar title="Tags">
          <v-btn prepend-icon="mdi-refresh" @click="fetchTags">Refresh</v-btn>
          <v-btn prepend-icon="mdi-delete" color="red" @click="deleteTags">Delete</v-btn>
          <v-dialog>
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" color="blue">
                <v-icon color="blue">mdi-plus</v-icon>
                Create
              </v-btn>
            </template>
            <template v-slot:default="{isActive}">
              <v-card class="pa-5">
                <v-col>
                  <h1>Create Tag</h1>
                  <ErrorPanel :error="error"></ErrorPanel>
                  <v-progress-linear v-if="creating" indeterminate :height="5"></v-progress-linear>
                  <EditTagForm
                    :tag="null"
                    @tag-save="createTag($event).then(success => {if (success) isActive.value = false})"
                  ></EditTagForm>
                </v-col>
              </v-card>
            </template>
          </v-dialog>
        </v-toolbar>
      </template>
    </v-data-table>
  </v-col>
</template>

<script lang="ts">
import {defineComponent, ref} from "vue"
import {Tag, UnsavedTag} from "../../components/models";
import EditTagForm from "../../components/admin/EditTagForm.vue";

export default defineComponent({
  components: {EditTagForm},
  data() {
    return {
      singleSelect: false,
      headers: [
        {
          title: "ID",
          align: "start",
          key: "id"
        },
        {title: "Label", key: "label"},
      ]
    }
  },
  setup() {
    const loading = ref(false)
    const creating = ref(false)
    const deleting = ref(false)
    const error = ref<Error | null>(null)
    const tags = ref<Tag[]>([])
    const selectedTags = ref<Tag[]>([])

    const fetchTags = async () => {
      loading.value = true
      try {
        const res = await fetch("/api/tag")
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          tags.value = await res.json()
        }
      } catch (err) {
        error.value = err
      }
      loading.value = false
    }

    const deleteTags = async () => {
      deleting.value = true
      try {
        const res = await fetch("/api/tag/bulk", {
          method: "DELETE",
          body: JSON.stringify({ids: selectedTags.value})
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          selectedTags.value = []
          fetchTags()
        }
      } catch (err) {
        error.value = err
      }
      deleting.value = false
    }

    const createTag = async (tag: UnsavedTag) => {
      creating.value = true
      const res = await fetch("/api/tag", {
        method: "POST",
        body: JSON.stringify(tag)
      })
      const success = res.ok;
      if (!success) {
        error.value = new Error(await res.text())
      } else {
        fetchTags()
      }
      creating.value = false
      return success
    }

    return {
      loading,
      creating,
      tags,
      selectedTags,
      error,
      fetchTags,
      createTag,
      deleteTags
    }
  },
  mounted() {
    this.fetchTags()
  }
})
</script>

<style scoped>

</style>
