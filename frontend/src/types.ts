/** API response types. Field names intentionally match the FastAPI contract. */
export interface CatalogOption {
  id: number
  name: string
  country?: string[]
  state?: string
}

export interface Catalog {
  domains: CatalogOption[]
  groups: CatalogOption[]
  traffic_sources: CatalogOption[]
}

export interface Offer {
  offer_id: number
  name: string
  share: number
  pinned: boolean
  removed: boolean
  new: boolean
  state: string
  removed_reason?: 'local' | 'source' | null
}

export interface Stream {
  id: number
  remote_id: number
  name: string
  editable: boolean
  dirty: boolean
  revision: number
  offers: Offer[]
  active_count: number
  total_share: number
  published_count: number
  source_missing: boolean
}

export interface CampaignSummary {
  id: number
  name: string
  alias: string
  domain_id: number
  group_id: number
  traffic_source_id: number
  state: string
  dirty_count?: number
}

export interface Campaign extends CampaignSummary {
  streams: Stream[]
  synced_at: string
  sync_changes?: string[]
}

export interface CreateCampaignRequest {
  name: string
  geo: string[]
  offer_id: number
  domain_id: number
  group_id: number
  traffic_source_id: number
}

export type OfferAction = 'add' | 'remove' | 'restore' | 'pin' | 'unpin'

export interface OfferMutation {
  action: OfferAction
  offer_id: number
  share?: number
}

export interface SyncConflict {
  message: string
  sync_conflict: true
  changes: string[]
  revisions: Record<number, number>
}

export interface HistoryEvent {
  id: number
  action: string
  stream_id: number | null
  details: { offer_id?: number; share?: number }
  created_at: string
}

export interface HealthStatus {
  auth_required: boolean
  campaign_name_prefix: string
}

export type WorkspacePage = 'campaigns' | 'create'
