import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import CampaignOverview from '../src/components/CampaignOverview.vue'
import { campaign, catalog } from './fixtures'

describe('Campaign link', () => {
  it('copies a complete URL when the tracker returns a domain without a scheme', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })
    const wrapper = mount(CampaignOverview, { props: { campaign: campaign(), catalog } })
    await wrapper.get('[aria-label="Скопировать ссылку кампании"]').trigger('click')
    await flushPromises()
    expect(writeText).toHaveBeenCalledWith('https://track.example.com/abc')
    expect(wrapper.text()).toContain('Скопировано')
  })

  it('keeps the URL available for manual copy if clipboard access is denied', async () => {
    vi.stubGlobal('navigator', {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
    })
    const wrapper = mount(CampaignOverview, { props: { campaign: campaign(), catalog } })
    await wrapper.get('[aria-label="Скопировать ссылку кампании"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('input').element.value).toBe('https://track.example.com/abc')
    expect(wrapper.text()).toContain('скопируйте её вручную')
  })
})
