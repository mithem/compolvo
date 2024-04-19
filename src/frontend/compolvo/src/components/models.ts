export interface AgentSoftware {
  id: string
  agent: Agent
  service_plan: string
  installed_version: string
  corrupt: boolean
  latest_version: string
  offering: ServiceOffering
  service: Service
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
  retrieval_method: number | null
  retrieval_data: string | null
  latest_version: string | null
  image: string | null
}

export interface Tag {
  id: string
  label: string
}

export interface DetailedService {
  id: string
  name: string
  description: string | null
  license: string | null
  download_count: number | null
  retrieval_method: number | null
  retrieval_data: string | null
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
