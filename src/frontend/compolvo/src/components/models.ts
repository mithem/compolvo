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
  props: { title: string }
}

export interface OperatingSystem {
  id: string
  props: { title: string }
}


export interface DetailedService {
  id: string
  name: string
  description: string | null
  operating_systems: string[] | null
  license: string | null
  download_count: number | null
  latest_version: string | null
  image: string | "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg"
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

export interface User {
  id: string;
  email: string
  first_name: string
  last_name: string
}
