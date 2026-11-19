import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App.vue'
import { useCampaignWorkspace } from '../src/composables/useCampaignWorkspace'
import { campaign, campaigns, catalog, stream } from './fixtures'

const api = vi.hoisted(() => ({
  getHealth: vi.fn(),
  getCatalog: vi.fn(),
  getCampaigns: vi.fn(),
  getCampaign: vi.fn(),
  editOffer: vi.fn(),
  cancelDraft: vi.fn(),
  searchOffers: vi.fn(),
}))

vi.mock('../src/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../src/api')>()),
  campaignApi: api,
}))

beforeEach(() => {
  location.hash = ''
  localStorage.clear()
  api.getHealth.mockResolvedValue({ auth_required: false, campaign_name_prefix: 'test_bakhshyan_' })
  api.getCatalog.mockResolvedValue(catalog)
  api.getCampaigns.mockResolvedValue(campaigns.map((item) => ({ ...item })))
  api.getCampaign.mockResolvedValue(campaign())
  api.searchOffers.mockResolvedValue([])
})

describe('Workspace continuity', () => {
  it('keeps an unfinished campaign form when navigating to the editor and back', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('.page-heading button').trigger('click')
    await wrapper.get('#campaign-name').setValue('beauty_ro')
    await wrapper.get('.form-footer .button.secondary').trigger('click')
    await wrapper.get('.page-heading button').trigger('click')
    expect(wrapper.get('#campaign-name').element.value).toBe('beauty_ro')
  })

  it('clears the campaign draft counter after cancelling a local edit', async () => {
    let workspace!: ReturnType<typeof useCampaignWorkspace>
    mount(
      defineComponent({
        setup() {
          workspace = useCampaignWorkspace()
          return () => null
        },
      }),
    )
    await flushPromises()
    const original = workspace.selectedCampaign.value!.streams[0]
    api.editOffer.mockResolvedValue(stream({ dirty: true, revision: 2 }))
    await workspace.editOffer(original, { action: 'pin', offer_id: 1 })
    expect(workspace.campaigns.value[0].dirty_count).toBe(1)
    workspace.pendingCancel.value = workspace.selectedCampaign.value!.streams[0]
    api.cancelDraft.mockResolvedValue(stream({ dirty: false, revision: 3 }))
    await workspace.confirmCancel()
    expect(workspace.campaigns.value[0].dirty_count).toBe(0)
  })
})
