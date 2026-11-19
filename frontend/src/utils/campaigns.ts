import type { CampaignSummary, Offer } from '../types'

export type CampaignScope = 'all' | 'own' | 'drafts'

export function matchesCampaign(
  campaign: CampaignSummary,
  query: string,
  scope: CampaignScope,
  namePrefix: string,
): boolean {
  const matchesQuery = `${campaign.name} ${campaign.id}`
    .toLocaleLowerCase('ru')
    .includes(query.trim().toLocaleLowerCase('ru'))
  const matchesScope =
    scope === 'all' ||
    (scope === 'own' && campaign.name.startsWith(namePrefix)) ||
    (scope === 'drafts' && (campaign.dirty_count ?? 0) > 0)

  return matchesQuery && matchesScope
}

export function matchesOffer(offer: Offer, query: string): boolean {
  return `${offer.name} ${offer.offer_id}`
    .toLocaleLowerCase('ru')
    .includes(query.trim().toLocaleLowerCase('ru'))
}
