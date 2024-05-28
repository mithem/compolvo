/* eslint-disable */
/* prettier-ignore */
// @ts-nocheck
// Generated by unplugin-vue-router. ‼️ DO NOT MODIFY THIS FILE ‼️
// It's recommended to commit this file.
// Make sure to add this file to your tsconfig.json file as an "includes" or "files" entry.

declare module 'vue-router/auto-routes' {
  import type {ParamValue, RouteRecordInfo,} from 'unplugin-vue-router/types'

  /**
   * Route name map generated by unplugin-vue-router
   */
  export interface RouteNamedMap {
    '/': RouteRecordInfo<'/', '/', Record<never, never>, Record<never, never>>,
    '/admin/': RouteRecordInfo<'/admin/', '/admin', Record<never, never>, Record<never, never>>,
    '/admin/service/[id]/': RouteRecordInfo<'/admin/service/[id]/', '/admin/service/:id', {
      id: ParamValue<true>
    }, { id: ParamValue<false> }>,
    '/admin/service/[id]/versions': RouteRecordInfo<'/admin/service/[id]/versions', '/admin/service/:id/versions', {
      id: ParamValue<true>
    }, { id: ParamValue<false> }>,
    '/admin/services': RouteRecordInfo<'/admin/services', '/admin/services', Record<never, never>, Record<never, never>>,
    '/agents': RouteRecordInfo<'/agents', '/agents', Record<never, never>, Record<never, never>>,
    '/compare': RouteRecordInfo<'/compare', '/compare', Record<never, never>, Record<never, never>>,
    '/detail': RouteRecordInfo<'/detail', '/detail', Record<never, never>, Record<never, never>>,
    '/home': RouteRecordInfo<'/home', '/home', Record<never, never>, Record<never, never>>,
    '/login': RouteRecordInfo<'/login', '/login', Record<never, never>, Record<never, never>>,
    '/logout': RouteRecordInfo<'/logout', '/logout', Record<never, never>, Record<never, never>>,
    '/payment-info': RouteRecordInfo<'/payment-info', '/payment-info', Record<never, never>, Record<never, never>>,
    '/profile': RouteRecordInfo<'/profile', '/profile', Record<never, never>, Record<never, never>>,
    '/register': RouteRecordInfo<'/register', '/register', Record<never, never>, Record<never, never>>,
    '/ServiceOfferingCard': RouteRecordInfo<'/ServiceOfferingCard', '/ServiceOfferingCard', Record<never, never>, Record<never, never>>,
  }
}
