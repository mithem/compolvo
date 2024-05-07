<script lang="ts">
import {defineComponent, getCurrentInstance, ref} from "vue"
import {UserMeObject} from "./models";
import {evaluatePasswordRules} from "./utils";

export default defineComponent({
  props: ["user"],
  data: () => ({
    newPasswordRules: [
      value => {
        if (value === "") return true
        return evaluatePasswordRules(value)
      }
    ],
    currentPasswordRules: [
      value => {
        if (value == "") return "Field is required."
        return true
      }
    ]
  }),
  setup(props: {
    user: UserMeObject
  }) {
    const user = ref(props.user);
    const didChangeInfo = ref(false);
    const currentPassword = ref("");
    const newPassword = ref("");
    const confirmPassword = ref("");
    const showingSnackbar = ref(false);
    const snackbarText = ref<string>(null);
    const oldUser = {...props.user}
    const deleting = ref(false);
    const error = ref<Error | null>(null);

    const confirmPasswordRules = [
      (value) => {
        if (value != newPassword.value) {
          return "New passwords do not match."
        }
        return true
      }
    ]

    const checkAuthStatus = async function (password: string) {
      try {
        const res = await fetch("/api/auth", {
          method: "POST",
          body: JSON.stringify({
            email: user.value.email,
            password: password
          })
        })
        return res.ok
      } catch (_) {
        return false
      }
    }

    let proxy = getCurrentInstance().proxy;

    const validate = async function () {
      const {valid: valid, errors: errors} = await proxy.$refs.form.validate()
      if (valid) {
        await saveInfo()
      } else {
        error.value = new Error("Error(s) valdiating form: " + errors.flatMap(err => err.errorMessages).join(", "))
      }
    }

    const saveInfo = async function () {
      const changedInfo = {
        first_name: user.value.first_name != oldUser.first_name ? user.value.first_name : undefined,
        last_name: user.value.last_name != oldUser.last_name ? user.value.last_name : undefined,
        email: user.value.email != oldUser.email ? user.value.email : undefined
      }

      if (newPassword.value !== "") {
        changedInfo["password"] = newPassword.value;
      }

      if (Object.values(changedInfo).every(value => value === undefined)) {
        snackbarText.value = "Info already up to date."
        showingSnackbar.value = true
        return
      }

      const authenticated = await checkAuthStatus(currentPassword.value);
      if (!authenticated) {
        error.value = new Error("Invalid password")
        return
      }

      try {
        const res = await fetch("/api/user?id=" + user.value.id, {
          method: "PATCH",
          body: JSON.stringify(changedInfo)
        })
        if (!res.ok) {
          error.value = new Error(await res.text())
        } else {
          didChangeInfo.value = false
          currentPassword.value = ""
          newPassword.value = ""
          confirmPassword.value = ""
          snackbarText.value = "Updated user info."
          showingSnackbar.value = true
        }
      } catch (err) {
        error.value = err
      }
    }

    const deleteAccount = async function () {
      deleting.value = true
      try {
        const me = await fetch("/api/user/me")
        const id = (await me.json()).id
        const res = await fetch("/api/user?id=" + id, {
          method: "DELETE"
        })
        deleting.value = false
        if (res.ok) {
          document.location.pathname = "/"
        } else {
          error.value = new Error(await res.text())
        }
      } catch (err) {
        error.value = err
      }
    }

    return {
      user,
      didChangeInfo,
      currentPassword,
      newPassword,
      confirmPassword,
      confirmPasswordRules,
      showingSnackbar,
      snackbarText,
      deleting,
      error,
      saveInfo,
      validate,
      deleteAccount
    }
  }
})
</script>

<template>
  <v-card class="form-card account-info-card">
    <v-card-title>Account info</v-card-title>
    <ErrorPanel v-if="error != null" :error="error" />
    <div class="payment-method-config-container">
      <div v-if="!user.has_payment_method">
        No payment method configured.
      </div>
      <div v-else class="payment-method-config-container no-space-between">
        <v-icon color="green">mdi-check</v-icon>
        Payment method configured.
      </div>
      <v-btn @click="$router.push('/payment-info')">
        Configure
      </v-btn>
    </div>
    <v-form
      fast-fail
      @submit.prevent
      @submit="validate"
      ref="form"
      validate-on="input"
    >
      <v-text-field
        v-model="user.first_name"
        label="First name"
        @change="didChangeInfo = true"
      ></v-text-field>

      <v-text-field
        v-model="user.last_name"
        label="Last name"
        @change="didChangeInfo = true"
      ></v-text-field>
      <v-text-field
        v-model="user.email"
        type="email"
        label="Email"
        @change="didChangeInfo = true"
      ></v-text-field>
      <v-text-field
        v-model="currentPassword"
        type="password"
        :rules="currentPasswordRules"
        label="Current password"
        mandatory
      ></v-text-field>
      <v-text-field v-if="currentPassword !== ''"
                    v-model="newPassword"
                    type="password"
                    :rules="newPasswordRules"
                    label="New password"
      ></v-text-field>
      <v-text-field v-if="currentPassword !== ''"
                    v-model="confirmPassword"
                    type="password"
                    label="Confirm password"
                    :rules="confirmPasswordRules"
                    validate-on="input"
      ></v-text-field>
      <v-card-actions>
        <v-btn type="submit">Save</v-btn>
        <v-spacer></v-spacer>
        <v-btn
          @click="deleteAccount"
          :loading=deleting
          color="red"
        >Delete account
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
  <v-snackbar
    v-model="showingSnackbar"
    :text="snackbarText"
    color="green"
  >
    <template v-slot:actions>
      <v-btn @click="showingSnackbar = false">Close</v-btn>
    </template>
  </v-snackbar>
</template>

<style scoped>
.account-info-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.payment-method-config-container {
  padding: 10px;
  display: flex;
  gap: 10px;
  justify-content: space-between;
}

.no-space-between {
  justify-content: normal;
}

.form-card {
  width: 100%;
}
</style>
