/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import {createVuetify} from 'vuetify'
import "@/styles/global.scss"

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme:'light',
    themes: {
      light: {
        dark: false,
        colors: {
          link: "#0d5aa7",
          "on-link": "#3288de"
        },
      },
      dark: {
        dark: true,
        colors: {
          link: "#3988DE",
          "on-link": "#50B3FA"
        }
      }
    }
  },
})
