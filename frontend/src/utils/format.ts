import type { Catalog } from '../types'

export function catalogName(catalog: Catalog, collection: keyof Catalog, id: number): string {
  return catalog[collection].find((item) => item.id === Number(id))?.name ?? '—'
}

export function formatTime(value: string): string {
  // SQLite stores UTC datetimes without a timezone suffix.
  const hasTimezone = value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value)
  const date = new Date(hasTimezone ? value : `${value}Z`)
  return new Intl.DateTimeFormat('ru', { hour: '2-digit', minute: '2-digit' }).format(date)
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.'
}
