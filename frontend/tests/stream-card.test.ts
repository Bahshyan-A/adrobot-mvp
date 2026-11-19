import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StreamCard from '../src/components/StreamCard.vue'
import { offer, stream } from './fixtures'

function mountStream(overrides: Parameters<typeof stream>[0] = {}) {
  return mount(StreamCard, {
    props: { stream: stream(overrides), position: 2, disabled: false, publishing: false },
  })
}

describe('Stream editor', () => {
  it('keeps archived offers available and finds them by ID', async () => {
    const wrapper = mountStream({
      offers: [offer(), offer({ offer_id: 2, name: 'Archived offer', removed: true, share: 0 })],
    })
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    await wrapper.get('.archive-toggle').trigger('click')
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    await wrapper.get('[aria-label="Найти оффер в потоке 402"]').setValue('2')
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.get('tbody tr').text()).toContain('Archived offer')
    await wrapper.get('.restore-button').trigger('click')
    expect(wrapper.emitted('mutate')).toEqual([[{ action: 'restore', offer_id: 2 }]])
    await wrapper.get('.archive-toggle').trigger('click')
    expect(wrapper.get('.archive-toggle').attributes('aria-expanded')).toBe('false')
  })

  it('automatically reveals an offer moved to the archive', async () => {
    const wrapper = mountStream()
    await wrapper.setProps({
      stream: stream({
        revision: 2,
        offers: [offer({ removed: true, share: 0 })],
        active_count: 0,
        total_share: 0,
        dirty: true,
      }),
    })
    expect(wrapper.get('.archive-toggle').attributes('aria-expanded')).toBe('true')
    expect(wrapper.text()).toContain('Вернуть')
  })

  it('allows explicit publication after removing every offer', async () => {
    const wrapper = mountStream({ dirty: true, total_share: 0, active_count: 0, offers: [] })
    const publishButton = wrapper.get('[title="Push to Keitaro"]')
    expect(publishButton.attributes('disabled')).toBeUndefined()
    expect(wrapper.text()).toContain('Все офферы будут убраны из потока в Keitaro')
    expect(wrapper.find('.distribution-heading .error-text').exists()).toBe(false)
    expect(wrapper.emitted('publish')).toBeUndefined()
    await publishButton.trigger('click')
    expect(wrapper.emitted('publish')).toEqual([[]])
  })

  it('still requires a total of 100% when active offers remain', async () => {
    const wrapper = mountStream({ dirty: true, total_share: 80, offers: [offer({ share: 80 })] })
    expect(wrapper.get('[title="Push to Keitaro"]').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Перед публикацией сумма долей должна составлять 100%')
    expect(wrapper.emitted('publish')).toBeUndefined()
  })

  it('emits explicit remove and pin actions from the offer row', async () => {
    const wrapper = mountStream()
    await wrapper.get('[aria-label="Закрепить долю оффера 1"]').trigger('click')
    await wrapper.get('[aria-label="Удалить оффер 1"]').trigger('click')
    expect(wrapper.emitted('mutate')).toEqual([
      [{ action: 'pin', offer_id: 1 }],
      [{ action: 'remove', offer_id: 1 }],
    ])
  })
})
