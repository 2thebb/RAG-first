'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import KoreaMap from '@/components/KoreaMap'
import ArtifactCard from '@/components/ArtifactCard'
import ArtifactDetail from '@/components/ArtifactDetail'
import FilterPanel from '@/components/FilterPanel'
import { Artifact, PROVINCE_MAP } from '@/lib/types'

interface FilterState {
  nationalityCode: string
  designationCode: string
  museumCode: string
  keyword: string
}

const PROVINCE_LAND_CODES: Record<string, string> = {
  서울특별시: 'GL05001',
  부산광역시: 'GL05002',
  대구광역시: 'GL05003',
  인천광역시: 'GL05004',
  광주광역시: 'GL05005',
  대전광역시: 'GL05006',
  울산광역시: 'GL05007',
  경기도: 'GL05008',
  강원도: 'GL05009',
  충청북도: 'GL05010',
  충청남도: 'GL05011',
  전라북도: 'GL05012',
  전라남도: 'GL05013',
  경상북도: 'GL05014',
  경상남도: 'GL05015',
  제주도: 'GL05016',
}

// GeoJSON province name → API province name 역매핑
const GEO_TO_API: Record<string, string> = {}
for (const [apiName, geoName] of Object.entries(PROVINCE_MAP)) {
  GEO_TO_API[geoName] = apiName
}

export default function Home() {
  const [allArtifacts, setAllArtifacts] = useState<Artifact[]>([])
  const [provinceArtifacts, setProvinceArtifacts] = useState<Record<string, Artifact[]>>({})
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null) // GeoJSON name
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [filters, setFilters] = useState<FilterState>({
    nationalityCode: '',
    designationCode: '',
    museumCode: '',
    keyword: '',
  })
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const fetchArtifacts = useCallback(
    async (currentFilters: FilterState, currentPage: number, append = false) => {
      setLoading(true)
      try {
        const params = new URLSearchParams({
          numOfRows: '100',
          pageNo: String(currentPage),
        })
        if (currentFilters.nationalityCode) params.set('nationalityCode', currentFilters.nationalityCode)
        if (currentFilters.designationCode) params.set('designationCode', currentFilters.designationCode)
        if (currentFilters.museumCode) params.set('museumCode', currentFilters.museumCode)
        if (currentFilters.keyword) params.set('name', currentFilters.keyword)

        const res = await fetch(`/api/artifacts?${params}`)
        const data = await res.json()

        if (data.list) {
          const artifacts: Artifact[] = data.list
          setTotalCount(data.totalCount || 0)
          setHasMore(currentPage * 100 < data.totalCount)

          const newArtifacts = append ? (prev: Artifact[]) => [...prev, ...artifacts] : artifacts
          setAllArtifacts(newArtifacts as Artifact[] | ((prev: Artifact[]) => Artifact[]))

          // 도별로 분류
          const byProvince: Record<string, Artifact[]> = append
            ? { ...provinceArtifacts }
            : {}

          for (const art of artifacts) {
            const landName = art.placeLandName1
            if (landName) {
              const geoName = PROVINCE_MAP[landName] || landName
              if (!byProvince[geoName]) byProvince[geoName] = []
              byProvince[geoName].push(art)
            }
          }

          setProvinceArtifacts({ ...byProvince })
        }
      } catch (error) {
        console.error('Failed to fetch artifacts:', error)
      } finally {
        setLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  // 초기 로드
  useEffect(() => {
    fetchArtifacts(filters, 1, false)
  }, []) // eslint-disable-line

  // 필터 변경 시 디바운스
  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setPage(1)
      fetchArtifacts(filters, 1, false)
    }, 400)
    return () => clearTimeout(debounceRef.current)
  }, [filters, fetchArtifacts])

  // 선택된 도의 유물 목록 (GeoJSON name 기준)
  const selectedArtifacts = selectedProvince
    ? provinceArtifacts[selectedProvince] || []
    : allArtifacts

  const selectedProvinceApiName = selectedProvince ? GEO_TO_API[selectedProvince] || selectedProvince : null

  const handleLoadMore = () => {
    const nextPage = page + 1
    setPage(nextPage)
    fetchArtifacts(filters, nextPage, true)
  }

  return (
    <div className="flex flex-col h-screen bg-[#080e1a]">
      {/* 헤더 */}
      <header className="bg-[#0a1020] border-b border-stone-800 px-6 py-3 flex items-center gap-4 flex-shrink-0">
        <div>
          <h1 className="text-lg font-bold text-amber-200 leading-tight">
            🏛 한국 유물 지도
          </h1>
          <p className="text-xs text-stone-500">이뮤지엄(e-Museum) 소장품 시각화</p>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-stone-400">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> 국보
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block ml-2" /> 보물
          <span className="w-2 h-2 rounded-full bg-teal-500 inline-block ml-2" /> 사적
        </div>
      </header>

      {/* 필터 */}
      <FilterPanel
        filters={filters}
        onFilterChange={setFilters}
        totalCount={totalCount}
        loading={loading}
      />

      {/* 메인 콘텐츠 */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* 지도 */}
        <div className="flex-shrink-0 w-[420px] xl:w-[500px] p-3">
          <KoreaMap
            provinceArtifacts={provinceArtifacts}
            selectedProvince={selectedProvince}
            onProvinceClick={setSelectedProvince}
            loading={loading}
          />
        </div>

        {/* 유물 목록 패널 */}
        <div className="flex-1 flex flex-col min-w-0 border-l border-stone-800">
          {/* 패널 헤더 */}
          <div className="px-4 py-3 border-b border-stone-800 flex items-center gap-2 flex-shrink-0">
            {selectedProvince ? (
              <>
                <button
                  onClick={() => setSelectedProvince(null)}
                  className="text-stone-400 hover:text-amber-300 text-sm"
                >
                  ← 전체
                </button>
                <span className="text-stone-600">|</span>
                <h2 className="text-sm font-semibold text-amber-200">
                  {selectedProvinceApiName}
                </h2>
                <span className="text-xs text-stone-400">
                  ({selectedArtifacts.length}점)
                </span>
              </>
            ) : (
              <h2 className="text-sm font-semibold text-stone-300">
                전체 유물{' '}
                <span className="text-amber-300">{allArtifacts.length.toLocaleString()}</span>점
                {totalCount > allArtifacts.length && (
                  <span className="text-stone-500"> / {totalCount.toLocaleString()}점</span>
                )}
              </h2>
            )}
          </div>

          {/* 유물 그리드 */}
          <div className="flex-1 overflow-y-auto p-3">
            {selectedArtifacts.length === 0 && !loading ? (
              <div className="flex flex-col items-center justify-center h-48 text-stone-500">
                <span className="text-4xl mb-3">🗺</span>
                <p className="text-sm">
                  {selectedProvince
                    ? '이 지역에 출토지가 기록된 유물이 없습니다'
                    : '유물을 불러오는 중...'}
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-[repeat(auto-fill,minmax(100px,1fr))] gap-2">
                  {selectedArtifacts.map((art) => (
                    <ArtifactCard
                      key={art.id}
                      artifact={art}
                      onClick={setSelectedArtifact}
                      size="md"
                    />
                  ))}
                </div>

                {/* 더 보기 버튼 */}
                {!selectedProvince && hasMore && (
                  <div className="mt-4 flex justify-center">
                    <button
                      onClick={handleLoadMore}
                      disabled={loading}
                      className="px-4 py-2 bg-stone-800 hover:bg-stone-700 text-stone-300 text-sm rounded-lg border border-stone-700 disabled:opacity-50"
                    >
                      {loading ? '로딩 중...' : '더 불러오기'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* 상세 모달 */}
      {selectedArtifact && (
        <ArtifactDetail
          artifact={selectedArtifact}
          onClose={() => setSelectedArtifact(null)}
        />
      )}
    </div>
  )
}
