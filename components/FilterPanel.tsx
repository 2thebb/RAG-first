'use client'

interface FilterState {
  nationalityCode: string
  designationCode: string
  museumCode: string
  keyword: string
}

interface FilterPanelProps {
  filters: FilterState
  onFilterChange: (filters: FilterState) => void
  totalCount: number
  loading: boolean
}

const DYNASTY_OPTIONS = [
  { code: '', label: '전체 시대' },
  { code: 'PS06001005', label: '고조선' },
  { code: 'PS06001009', label: '백제' },
  { code: 'PS06001010', label: '신라' },
  { code: 'PS06001011', label: '고구려' },
  { code: 'PS06001008', label: '가야' },
  { code: 'PS06001012', label: '통일신라' },
  { code: 'PS06001013', label: '발해' },
  { code: 'PS06001014', label: '고려' },
  { code: 'PS06001018', label: '조선' },
  { code: 'PS06001019', label: '대한제국' },
]

const DESIGNATION_OPTIONS = [
  { code: '', label: '전체' },
  { code: 'PS12001', label: '국보' },
  { code: 'PS12002', label: '보물' },
  { code: 'PS12003', label: '사적' },
  { code: 'PS12004', label: '천연기념물' },
]

const MUSEUM_OPTIONS = [
  { code: '', label: '전체 박물관' },
  { code: 'PS01001001', label: '국립중앙박물관' },
  { code: 'PS01001002', label: '국립민속박물관' },
  { code: 'PS01001003', label: '국립경주박물관' },
  { code: 'PS01001004', label: '국립광주박물관' },
  { code: 'PS01001005', label: '국립전주박물관' },
  { code: 'PS01001006', label: '국립부여박물관' },
  { code: 'PS01001007', label: '국립공주박물관' },
  { code: 'PS01001008', label: '국립청주박물관' },
  { code: 'PS01001009', label: '국립대구박물관' },
  { code: 'PS01001010', label: '국립김해박물관' },
  { code: 'PS01001011', label: '국립제주박물관' },
  { code: 'PS01001012', label: '국립춘천박물관' },
]

export default function FilterPanel({ filters, onFilterChange, totalCount, loading }: FilterPanelProps) {
  const update = (key: keyof FilterState, value: string) => {
    onFilterChange({ ...filters, [key]: value })
  }

  return (
    <div className="bg-[#0d1624] border-b border-stone-800 px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-3">
        {/* 검색 */}
        <div className="relative flex-1 min-w-48">
          <input
            type="text"
            placeholder="유물 이름 검색..."
            value={filters.keyword}
            onChange={(e) => update('keyword', e.target.value)}
            className="w-full bg-stone-800/60 border border-stone-700 rounded-lg px-3 py-1.5 text-sm text-stone-200 placeholder-stone-500 focus:outline-none focus:border-amber-500"
          />
        </div>

        {/* 시대 */}
        <select
          value={filters.nationalityCode}
          onChange={(e) => update('nationalityCode', e.target.value)}
          className="bg-stone-800/60 border border-stone-700 rounded-lg px-3 py-1.5 text-sm text-stone-200 focus:outline-none focus:border-amber-500 cursor-pointer"
        >
          {DYNASTY_OPTIONS.map((o) => (
            <option key={o.code} value={o.code} className="bg-stone-900">
              {o.label}
            </option>
          ))}
        </select>

        {/* 문화재 지정 */}
        <select
          value={filters.designationCode}
          onChange={(e) => update('designationCode', e.target.value)}
          className="bg-stone-800/60 border border-stone-700 rounded-lg px-3 py-1.5 text-sm text-stone-200 focus:outline-none focus:border-amber-500 cursor-pointer"
        >
          {DESIGNATION_OPTIONS.map((o) => (
            <option key={o.code} value={o.code} className="bg-stone-900">
              {o.label}
            </option>
          ))}
        </select>

        {/* 박물관 */}
        <select
          value={filters.museumCode}
          onChange={(e) => update('museumCode', e.target.value)}
          className="bg-stone-800/60 border border-stone-700 rounded-lg px-3 py-1.5 text-sm text-stone-200 focus:outline-none focus:border-amber-500 cursor-pointer"
        >
          {MUSEUM_OPTIONS.map((o) => (
            <option key={o.code} value={o.code} className="bg-stone-900">
              {o.label}
            </option>
          ))}
        </select>

        {/* 결과 수 */}
        <div className="ml-auto text-xs text-stone-400">
          {loading ? (
            <span className="text-amber-400 animate-pulse">로딩 중...</span>
          ) : (
            <span>
              총 <span className="text-amber-300 font-semibold">{totalCount.toLocaleString()}</span>점
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
