export interface AgentSoftware {
  id: string
  agent: Agent
  service_plan: string
  installed_version: string
  corrupt: boolean
  latest_version: string
  offering: ServiceOffering
  service: AgentService
}

export interface ServiceOffering {
  id: string
  name: string
  description: string
  price: number
  duration_days: number
  service: string
}

export interface AgentService {
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

export interface User {
  id: string;
  email: string
  first_name: string
  last_name: string
}
