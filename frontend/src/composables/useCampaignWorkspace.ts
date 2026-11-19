import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ApiError, campaignApi } from '../api'
import type {
  Campaign,
  CampaignSummary,
  Catalog,
  CreateCampaignRequest,
  HistoryEvent,
  OfferMutation,
  Stream,
  SyncConflict,
  WorkspacePage,
} from '../types'
import { errorMessage } from '../utils/format'

function pageFromHash(): WorkspacePage {
  return location.hash === '#create' ? 'create' : 'campaigns'
}

/** Coordinates API operations; form inputs and row editing stay inside their components. */
export function useCampaignWorkspace() {
  const page = ref<WorkspacePage>(pageFromHash())
  const campaignNamePrefix = ref('')
  const catalog = ref<Catalog>({ domains: [], groups: [], traffic_sources: [] })
  const campaigns = ref<CampaignSummary[]>([])
  const selectedCampaign = ref<Campaign | null>(null)
  const isLoading = ref(true)
  const isBusy = ref(false)
  const pendingStreamId = ref<number | null>(null)
  const needsAuthentication = ref(false)
  const error = ref('')
  const notification = ref('')
  const syncChanges = ref<string[]>([])
  const syncConflict = ref<SyncConflict | null>(null)
  const pendingCancel = ref<Stream | null>(null)
  const history = ref<HistoryEvent[] | null>(null)
  let notificationTimer: ReturnType<typeof setTimeout> | undefined

  function notify(message: string): void {
    notification.value = message
    clearTimeout(notificationTimer)
    notificationTimer = setTimeout(() => (notification.value = ''), 4500)
  }

  function navigate(nextPage: WorkspacePage): void {
    page.value = nextPage
    location.hash = nextPage
    error.value = ''
  }

  function handleHashChange(): void {
    page.value = pageFromHash()
  }

  function setSelectedCampaign(campaign: Campaign): void {
    selectedCampaign.value = campaign
    updateDraftCount(campaign)
    localStorage.setItem('selected-campaign', String(campaign.id))
  }

  function updateDraftCount(selected: Campaign): void {
    const dirtyCount = selected.streams.filter((stream) => stream.dirty).length
    campaigns.value = campaigns.value.map((campaign) =>
      campaign.id === selected.id ? { ...campaign, dirty_count: dirtyCount } : campaign,
    )
  }

  async function execute(operation: () => Promise<void>): Promise<void> {
    error.value = ''
    isBusy.value = true
    try {
      await operation()
    } catch (cause) {
      error.value = errorMessage(cause)
      if (cause instanceof ApiError && cause.status === 401) {
        needsAuthentication.value = true
      }
    } finally {
      isBusy.value = false
    }
  }

  async function loadWorkspace(): Promise<void> {
    isLoading.value = true
    await execute(async () => {
      const health = await campaignApi.getHealth()
      campaignNamePrefix.value = health.campaign_name_prefix
      needsAuthentication.value = health.auth_required && !sessionStorage.getItem('app-token')
      if (needsAuthentication.value) return

      const [loadedCatalog, loadedCampaigns] = await Promise.all([
        campaignApi.getCatalog(),
        campaignApi.getCampaigns(),
      ])
      catalog.value = loadedCatalog
      campaigns.value = loadedCampaigns

      const preferredId =
        selectedCampaign.value?.id ?? Number(localStorage.getItem('selected-campaign'))
      const preferredCampaign = loadedCampaigns.find((campaign) => campaign.id === preferredId)
      const initialCampaign = preferredCampaign ?? loadedCampaigns[0]
      if (initialCampaign) {
        setSelectedCampaign(await campaignApi.getCampaign(initialCampaign.id))
      } else {
        selectedCampaign.value = null
      }
    })
    isLoading.value = false
  }

  async function login(token: string): Promise<void> {
    sessionStorage.setItem('app-token', token)
    await loadWorkspace()
    if (needsAuthentication.value) sessionStorage.removeItem('app-token')
  }

  async function selectCampaign(id: number): Promise<void> {
    await execute(async () => {
      setSelectedCampaign(await campaignApi.getCampaign(id))
      syncChanges.value = []
    })
  }

  async function createCampaign(body: CreateCampaignRequest): Promise<void> {
    await execute(async () => {
      const created = await campaignApi.createCampaign(body)
      setSelectedCampaign(created)
      // Keep the successful result visible even if refreshing the list later fails.
      campaigns.value = [...campaigns.value, created]
      navigate('campaigns')
      notify('Кампания создана. Оба потока настроены.')
    })
  }

  async function fetchStreams(discardDrafts = false): Promise<void> {
    if (!selectedCampaign.value) return
    isBusy.value = true
    error.value = ''
    try {
      const revisions = discardDrafts ? syncConflict.value?.revisions : undefined
      const updated = await campaignApi.fetchStreams(selectedCampaign.value.id, revisions)
      setSelectedCampaign(updated)
      syncChanges.value = updated.sync_changes ?? []
      syncConflict.value = null
      notify('Потоки загружены из Keitaro')
    } catch (cause) {
      if (cause instanceof ApiError && cause.conflict) {
        syncConflict.value = cause.conflict
      } else {
        error.value = errorMessage(cause)
      }
    } finally {
      isBusy.value = false
    }
  }

  function replaceStream(updatedStream: Stream): void {
    if (!selectedCampaign.value) return
    selectedCampaign.value.streams = selectedCampaign.value.streams.map((stream) =>
      stream.id === updatedStream.id ? updatedStream : stream,
    )
    updateDraftCount(selectedCampaign.value)
  }

  async function mutateStream(
    stream: Stream,
    operation: () => Promise<Stream>,
    successMessage?: string,
  ): Promise<boolean> {
    if (isBusy.value || pendingStreamId.value !== null) return false
    pendingStreamId.value = stream.id
    error.value = ''
    try {
      replaceStream(await operation())
      if (successMessage) notify(successMessage)
      return true
    } catch (cause) {
      error.value = errorMessage(cause)
      return false
    } finally {
      pendingStreamId.value = null
    }
  }

  async function editOffer(stream: Stream, mutation: OfferMutation): Promise<void> {
    await mutateStream(stream, () => campaignApi.editOffer(stream, mutation))
  }

  async function publishStream(stream: Stream): Promise<void> {
    await mutateStream(
      stream,
      () => campaignApi.publishStream(stream),
      'Изменения опубликованы в Keitaro',
    )
  }

  async function confirmCancel(): Promise<void> {
    const stream = pendingCancel.value
    if (!stream) return
    const succeeded = await mutateStream(
      stream,
      () => campaignApi.cancelDraft(stream),
      'Черновик отменён',
    )
    if (succeeded) pendingCancel.value = null
  }

  async function loadHistory(): Promise<void> {
    if (!selectedCampaign.value) return
    const campaignId = selectedCampaign.value.id
    await execute(async () => {
      history.value = await campaignApi.getHistory(campaignId)
    })
  }

  onMounted(() => {
    void loadWorkspace()
    window.addEventListener('hashchange', handleHashChange)
  })

  onBeforeUnmount(() => {
    clearTimeout(notificationTimer)
    window.removeEventListener('hashchange', handleHashChange)
  })

  return {
    page,
    campaignNamePrefix,
    catalog,
    campaigns,
    selectedCampaign,
    isLoading,
    isBusy,
    pendingStreamId,
    needsAuthentication,
    error,
    notification,
    syncChanges,
    syncConflict,
    pendingCancel,
    history,
    navigate,
    loadWorkspace,
    login,
    selectCampaign,
    createCampaign,
    fetchStreams,
    editOffer,
    publishStream,
    confirmCancel,
    loadHistory,
  }
}
