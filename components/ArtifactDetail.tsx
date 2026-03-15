'use client'

import { useState, useEffect } from 'react'
import { Artifact, DESIGNATION_COLORS } from '@/lib/types'

interface ArtifactDetailProps {
  artifact: Artifact
  onClose: () => void
}

interface DetailData extends Artifact {
  imageList?: {
    totalCount: number
    list: { imgId: string; imgOrder: number; imgUri: string; imgThumUriM: string }[]
  }
}

export default function ArtifactDetail({ artifact, onClose }: ArtifactDetailProps) {
  const [detail, setDetail] = useState<DetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeImg, setActiveImg] = useState<string>('')

  useEffect(() => {
    setLoading(true)
    fetch(`/api/detail?id=${artifact.id}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.list?.[0]) {
          const d = data.list[0] as DetailData
          d.imageList = data.imageList
          setDetail(d)
          setActiveImg(d.imgUri || d.imgThumUriL || d.imgThumUriM || '')
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [artifact.id])

  const designColor = detail?.designationName1
    ? DESIGNATION_COLORS[detail.designationName1] || '#888'
    : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 배경 */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* 모달 */}
      <div className="relative bg-[#12192b] border border-stone-700 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto z-10">
        {/* 헤더 */}
        <div className="sticky top-0 bg-[#12192b]/95 backdrop-blur px-6 py-4 border-b border-stone-700 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-amber-100">{artifact.nameKr}</h2>
              {designColor && (
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ backgroundColor: designColor + '33', color: designColor }}
                >
                  {detail?.designationName1 || artifact.designationName1}
                </span>
              )}
            </div>
            {artifact.nameCn && (
              <p className="text-stone-400 text-sm mt-0.5">{artifact.nameCn}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-white text-2xl leading-none ml-4 mt-1"
          >
            ×
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-amber-300 animate-pulse">상세 정보 로딩 중...</div>
          </div>
        ) : detail ? (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 이미지 영역 */}
            <div>
              <div className="bg-stone-900 rounded-xl overflow-hidden aspect-square flex items-center justify-center mb-3">
                {activeImg ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={activeImg}
                    alt={detail.nameKr}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <span className="text-6xl">🏺</span>
                )}
              </div>
              {/* 이미지 목록 */}
              {detail.imageList && detail.imageList.totalCount > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {detail.imageList.list.map((img) => (
                    <button
                      key={img.imgId}
                      onClick={() => setActiveImg(img.imgUri || img.imgThumUriM)}
                      className={`
                        flex-shrink-0 w-14 h-14 rounded-lg overflow-hidden border-2
                        ${activeImg === (img.imgUri || img.imgThumUriM) ? 'border-amber-400' : 'border-stone-700'}
                      `}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={img.imgThumUriM}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* 정보 영역 */}
            <div className="space-y-3">
              <InfoRow label="박물관" value={[detail.museumName2, detail.museumName3].filter(Boolean).join(' · ')} />
              <InfoRow label="시대" value={[detail.nationalityName1, detail.nationalityName2].filter(Boolean).join(' · ')} />
              <InfoRow label="작가/제작자" value={detail.author} />
              <InfoRow label="재질" value={[detail.materialName1, detail.materialName2].filter(Boolean).join(' > ')} />
              <InfoRow
                label="용도/분류"
                value={[detail.purposeName1, detail.purposeName2, detail.purposeName3]
                  .filter(Boolean)
                  .join(' > ')}
              />
              <InfoRow
                label="출토지"
                value={[detail.placeLandName1, detail.placeLandName2].filter(Boolean).join(' ')}
              />
              <InfoRow label="크기" value={detail.sizeInfo} />
              <InfoRow label="소장품 번호" value={detail.relicNo} />
              {detail.indexWord && (
                <div>
                  <p className="text-stone-500 text-xs mb-1">태그</p>
                  <div className="flex flex-wrap gap-1">
                    {detail.indexWord.split(',').map((tag, i) => (
                      <span
                        key={i}
                        className="text-xs bg-stone-800 text-stone-300 px-2 py-0.5 rounded-full"
                      >
                        {tag.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {detail.desc && (
                <div>
                  <p className="text-stone-500 text-xs mb-1">설명</p>
                  <p
                    className="text-stone-300 text-xs leading-relaxed max-h-32 overflow-y-auto"
                    dangerouslySetInnerHTML={{ __html: detail.desc }}
                  />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-6 text-stone-400 text-center">상세 정보를 불러올 수 없습니다.</div>
        )}
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null
  return (
    <div>
      <p className="text-stone-500 text-xs">{label}</p>
      <p className="text-stone-200 text-sm">{value}</p>
    </div>
  )
}
