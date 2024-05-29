export interface AgentSoftware {
  id: string
  agent: Agent
  service_plan: string
  installed_version: string
  corrupt: boolean
  latest_version: string
  offering: ServiceOffering
  service: Service
  installing: boolean
  uninstalling: boolean
  last_updated: Date
}

export interface PackageManager {
  id: string
  name: string
}

export interface ServerStatus {
  id: string
  server_id: string
  server_running: boolean
  performing_billing_maintenance: boolean
}

export interface PackageManagerAvailableVersion {
  id: string
  version: string
  operating_system: OperatingSystem
  package_manager: PackageManager
}

export interface ServiceOffering {
  id: string
  name: string
  description: string
  price: number
  duration_days: number
  service: string
}

export interface DetailedServiceOffering {
  id: string
  name: string
  description: string
  price: number
  duration_days: number
  service: Service
}

export interface Service {
  id: string
  name: string
  description: string | null
  license: string | null
  download_count: number | null
  image: string | null
}

export interface Tag {
  id: string
  props: { title: string }
}

export interface License {
  id: string
  props: { title: string, subtitle: string | undefined }
}

export interface OperatingSystem {
  id: string
  props: { title: string }
  system_name: string
}


export interface DetailedService {
  id: string
  name: string
  system_name: string
  description: string | null
  short_description: string | null
  operating_systems: string[] | null
  license: string | null
  download_count: number | null
  tags: Tag[]
  offerings: ServiceOffering[]
}

export interface Agent {
  id: string;
  name: string;
  user: string;
  lastConnectionStart: Date;
  lastConnectionEnd: Date;
  connected: boolean;
  connectionInterrupted: boolean;
  initialized: boolean;
}

export interface ServicePlan {
  id: string
  user: string
  service_offering: DetailedServiceOffering
  start_date: string
  end_date: string
  canceled_by_user: boolean
  installable: boolean
}

export interface UserRole {
  id: string
  role: number
}

export enum BillingCylce {
  INDIVIDUAL
}

export interface UserMeObject {
  id: string
  first_name: string
  last_name: string
  email: string
  roles: UserRole[]
  connected_to_billing_provider: boolean
  has_payment_method: boolean
  billing_cycle: BillingCylce
}

export interface Token {
  id: string
  expires: Date
}
