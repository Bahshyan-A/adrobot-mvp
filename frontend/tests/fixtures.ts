import type { Campaign, CampaignSummary, Catalog, Offer, Stream } from '../src/types'

export const catalog: Catalog = {
  domains: [{ id: 1, name: 'track.example.com' }],
  groups: [{ id: 1, name: 'FORTESTS' }],
  traffic_sources: [{ id: 1, name: 'Meta Ads' }],
}

export function offer(overrides: Partial<Offer> = {}): Offer {
  return {
    offer_id: 1,
    name: 'Beauty Romania',
    share: 100,
    pinned: false,
    removed: false,
    new: false,
    state: 'active',
    removed_reason: null,
    ...overrides,
  }
}

export function stream(overrides: Partial<Stream> = {}): Stream {
  return {
    id: 1,
    remote_id: 402,
    name: 'Основной поток',
    editable: true,
    dirty: false,
    revision: 1,
    offers: [offer()],
    active_count: 1,
    total_share: 100,
    published_count: 1,
    source_missing: false,
    ...overrides,
  }
}

export const campaigns: CampaignSummary[] = [
  {
    id: 128,
    name: 'test_bakhshyan_campaign1',
    alias: 'abc',
    domain_id: 1,
    group_id: 1,
    traffic_source_id: 1,
    state: 'active',
    dirty_count: 1,
  },
  {
    id: 129,
    name: 'Other campaign',
    alias: 'other',
    domain_id: 1,
    group_id: 1,
    traffic_source_id: 1,
    state: 'active',
    dirty_count: 0,
  },
]

export function campaign(overrides: Partial<Campaign> = {}): Campaign {
  return {
    ...campaigns[0],
    streams: [stream()],
    synced_at: '2026-11-19T09:00:00Z',
    ...overrides,
  }
}
