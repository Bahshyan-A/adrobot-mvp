import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CampaignBrowser from '../src/components/CampaignBrowser.vue'
import { campaigns } from './fixtures'

function mountBrowser() {
  return mount(CampaignBrowser, {
    props: { campaigns, selectedId: 128, namePrefix: 'test_bakhshyan_', disabled: false },
  })
}

describe('Campaign selection', () => {
  it('filters own campaigns and searches by ID without changing the selection', async () => {
    const wrapper = mountBrowser()
    expect(wrapper.findAll('.campaign-item')).toHaveLength(2)
    await wrapper.findAll('.scope-filters button')[1].trigger('click')
    expect(wrapper.findAll('.campaign-item')).toHaveLength(1)
    expect(wrapper.get('.campaign-item').text()).toContain('test_bakhshyan_campaign1')
    expect(wrapper.emitted('select')).toBeUndefined()

    await wrapper.get('input').setValue('128')
    expect(wrapper.findAll('.campaign-item')).toHaveLength(1)
    await wrapper.get('input').setValue('129')
    expect(wrapper.findAll('.campaign-item')).toHaveLength(0)
    expect(wrapper.text()).toContain('Кампании не найдены')
  })

  it('updates the drafts filter after a draft is published or cancelled', async () => {
    const wrapper = mountBrowser()
    await wrapper.findAll('.scope-filters button')[2].trigger('click')
    expect(wrapper.findAll('.campaign-item')).toHaveLength(1)
    await wrapper.setProps({
      campaigns: campaigns.map((campaign) => ({ ...campaign, dirty_count: 0 })),
    })
    expect(wrapper.findAll('.campaign-item')).toHaveLength(0)
  })

  it('selects a campaign only on an explicit click and respects disabled controls', async () => {
    const wrapper = mountBrowser()
    await wrapper.findAll('.campaign-item')[1].trigger('click')
    expect(wrapper.emitted('select')).toEqual([[129]])
    await wrapper.setProps({ disabled: true })
    await wrapper.findAll('.campaign-item')[0].trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })
})
