<template>
  <v-card class="form-card account-info-card">
    <v-card-title>Account info</v-card-title>
    <ErrorPanel v-if="error != null" :error="error"/>
    <v-alert
      v-if="!user.email_verified"
      type="warning"
    >
      <v-row align="center">
        <v-col class="grow">
          Email not verified. Please verify your email address.
        </v-col>
        <v-col class="shrink">
          <v-btn
            @click="verifyEmailAddress"
            :loading="verifyingEmail"
          >Verify
          </v-btn>
        </v-col>
      </v-row>
    </v-alert>
    <div class="payment-method-config-container">
      <div v-if="!user.has_payment_method">
        No payment method configured.
      </div>
      <div v-else class="payment-method-config-container no-space-between">
        <v-icon color="green">mdi-check</v-icon>
        Payment method configured.
      </div>
      <v-spacer></v-spacer>
      <v-btn
        v-if="user.has_payment_method"
        variant="text"
        :loading="deletingPaymentMethod"
        @click="deletePaymentMethod"
      >
        <v-icon color="red">mdi-delete</v-icon>
      </v-btn>
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
      <v-text-field
        v-model="newPassword"
        type="password"
        :rules="newPasswordRules"
        label="New password"
      ></v-text-field>
      <v-text-field
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
    const deletingPaymentMethod = ref(false);
    const proxy = getCurrentInstance().proxy;
    const verifyingEmail = ref(false);

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


    const validate = async function () {
      const {valid: valid, errors: errors} = await proxy.$refs.form.validate()
      if (valid) {
        await saveInfo()
      } else {
        error.value = new Error("Error(s) valdiating form: " + errors.flatMap(err => err.errorMessages).join(", "))
      }
    }

    const deletePaymentMethod = async function () {
      const res = await fetch("/api/billing/payment/method/all", {
        method: "DELETE"
      })
      if (!res.ok) {
        error.value = new Error(await res.text())
      } else {
        user.value.has_payment_method = false
        snackbarText.value = "Deleted payment method."
        showingSnackbar.value = true
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
          let text = "Updated user info."
          if (changedInfo["password"] !== undefined) {
            text += " Please login again."
            setTimeout(() => {
              proxy.$router.push({path: "/login", query: {redirect_url: "/profile?showForm=true"}})
            }, 1500)
          }
          snackbarText.value = text
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

    const verifyEmailAddress = async function () {
      verifyingEmail.value = true
      try {
        const res = await fetch("/api/user/email/verify", {
          method: "POST"
        })
        if (res.ok) {
          snackbarText.value = "Verification email sent."
          showingSnackbar.value = true
        } else {
          error.value = new Error(await res.text())
        }
      } catch (err) {
        error.value = err
      }
      verifyingEmail.value = false
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
      deletingPaymentMethod,
      error,
      verifyingEmail,
      saveInfo,
      validate,
      deleteAccount,
      deletePaymentMethod,
      verifyEmailAddress
    }
  }
})
</script>


<style scoped>
.account-info-card {
  display: flex;
  flex-direction: column;
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
