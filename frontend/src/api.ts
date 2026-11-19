import type {
  Campaign,
  CampaignSummary,
  Catalog,
  CatalogOption,
  CreateCampaignRequest,
  HealthStatus,
  HistoryEvent,
  OfferMutation,
  Stream,
  SyncConflict,
} from './types'

interface ValidationError {
  msg: string
}

interface ErrorResponse {
  detail?: string | ValidationError[] | SyncConflict
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly conflict?: SyncConflict,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function parseApiError(data: ErrorResponse, status: number): ApiError {
  const detail = data.detail
  if (Array.isArray(detail)) {
    const message = detail.map((error) => error.msg.replace('Value error, ', '')).join('. ')
    return new ApiError(message, status)
  }
  if (typeof detail === 'object' && detail?.sync_conflict) {
    return new ApiError(detail.message, status, detail)
  }
  return new ApiError(
    typeof detail === 'string' ? detail : 'Не удалось выполнить запрос. Повторите попытку.',
    status,
  )
}

async function request<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const token = sessionStorage.getItem('app-token')
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })

  let data: unknown
  try {
    data = await response.json()
  } catch {
    throw new ApiError('Сервер вернул некорректный ответ. Проверьте подключение.', response.status)
  }
  if (!response.ok) {
    throw parseApiError(data as ErrorResponse, response.status)
  }
  return data as T
}

export const campaignApi = {
  getHealth: () => request<HealthStatus>('/health'),
  getCatalog: () => request<Catalog>('/catalog'),
  getCampaigns: () => request<CampaignSummary[]>('/campaigns'),
  getCampaign: (id: number) => request<Campaign>(`/campaigns/${id}`),
  createCampaign: (body: CreateCampaignRequest) => request<Campaign>('/campaigns', body),
  searchOffers: (query: string, signal: AbortSignal) =>
    request<CatalogOption[]>(`/offers?q=${encodeURIComponent(query)}`, undefined, signal),
  fetchStreams: (id: number, revisions?: Record<number, number>) =>
    request<Campaign>(`/campaigns/${id}/fetch`, {
      discard_drafts: revisions !== undefined,
      revisions: revisions ?? {},
    }),
  editOffer: (stream: Stream, mutation: OfferMutation) =>
    request<Stream>(`/streams/${stream.id}/offers`, { ...mutation, revision: stream.revision }),
  publishStream: (stream: Stream) =>
    request<Stream>(`/streams/${stream.id}/push`, { revision: stream.revision }),
  cancelDraft: (stream: Stream) =>
    request<Stream>(`/streams/${stream.id}/cancel`, { revision: stream.revision }),
  getHistory: (campaignId: number) => request<HistoryEvent[]>(`/campaigns/${campaignId}/history`),
}
