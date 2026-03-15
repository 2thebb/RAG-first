const BASE_URL = 'https://www.emuseum.go.kr/openapi'

export function buildImageUrl(relativeUrl: string, serviceKey: string): string {
  if (!relativeUrl) return ''
  if (relativeUrl.startsWith('http')) return relativeUrl
  // 상대경로인 경우 절대경로로 변환
  return `https://www.emuseum.go.kr${relativeUrl.startsWith('/') ? '' : '/'}${relativeUrl}`
}

export function normalizeArtifactImages<T extends Record<string, unknown>>(item: T): T {
  const fields = ['imgUri', 'imgThumUriS', 'imgThumUriM', 'imgThumUriL'] as const
  const result = { ...item }
  for (const field of fields) {
    const val = result[field] as string | undefined
    if (val && !val.startsWith('http')) {
      ;(result as Record<string, unknown>)[field] = `https://www.emuseum.go.kr/${val.replace(/^\//, '')}`
    }
  }
  return result
}

export interface ListParams {
  serviceKey: string
  numOfRows?: number
  pageNo?: number
  name?: string
  nameKr?: string
  nationalityCode?: string
  materialCode?: string
  purposeCode?: string
  placeLandCode?: string
  designationCode?: string
  museumCode?: string
  indexWord?: string
}

const JSON_HEADERS = { Accept: 'application/json' }

export async function fetchRelicList(params: ListParams) {
  const url = new URL(`${BASE_URL}/relic/list`)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') url.searchParams.set(k, String(v))
  })
  const res = await fetch(url.toString(), {
    headers: JSON_HEADERS,
    next: { revalidate: 300 },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchRelicDetail(serviceKey: string, id: string) {
  const url = new URL(`${BASE_URL}/relic/detail`)
  url.searchParams.set('serviceKey', serviceKey)
  url.searchParams.set('id', id)
  const res = await fetch(url.toString(), {
    headers: JSON_HEADERS,
    next: { revalidate: 3600 },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchCodes(serviceKey: string, parentCode?: string) {
  const url = new URL(`${BASE_URL}/code`)
  url.searchParams.set('serviceKey', serviceKey)
  url.searchParams.set('numOfRows', '100')
  if (parentCode) url.searchParams.set('parentCode', parentCode)
  const res = await fetch(url.toString(), {
    headers: JSON_HEADERS,
    next: { revalidate: 86400 },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
