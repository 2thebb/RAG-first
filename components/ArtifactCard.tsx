'use client'

import { useState } from 'react'
import { Artifact, DESIGNATION_COLORS } from '@/lib/types'

interface ArtifactCardProps {
  artifact: Artifact
  onClick: (artifact: Artifact) => void
  size?: 'sm' | 'md' | 'lg'
}

export default function ArtifactCard({ artifact, onClick, size = 'md' }: ArtifactCardProps) {
  const [imgError, setImgError] = useState(false)
  const imgSrc = artifact.imgThumUriM || artifact.imgThumUriL || artifact.imgThumUriS

  const designColor = artifact.designationName1
    ? DESIGNATION_COLORS[artifact.designationName1] || '#888'
    : null

  const sizeClasses = {
    sm: 'w-20 h-20',
    md: 'w-28 h-28',
    lg: 'w-36 h-36',
  }

  return (
    <div
      className={`
        relative group cursor-pointer rounded-lg overflow-hidden
        border border-stone-700 hover:border-amber-400
        transition-all duration-200 hover:scale-105 hover:shadow-xl hover:shadow-amber-900/30
        ${sizeClasses[size]}
      `}
      onClick={() => onClick(artifact)}
    >
      {imgSrc && !imgError ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={imgSrc}
          alt={artifact.nameKr}
          className="w-full h-full object-cover"
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="w-full h-full bg-stone-800 flex items-center justify-center">
          <span className="text-3xl">🏺</span>
        </div>
      )}

      {/* 호버 오버레이 */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/60 transition-all duration-200 flex items-end">
        <div className="p-1.5 w-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <p className="text-white text-xs font-medium truncate leading-tight">
            {artifact.nameKr}
          </p>
          {artifact.nationalityName2 && (
            <p className="text-amber-300 text-[10px] truncate">{artifact.nationalityName2}</p>
          )}
        </div>
      </div>

      {/* 문화재 지정 뱃지 */}
      {designColor && (
        <div
          className="absolute top-1 right-1 w-2 h-2 rounded-full shadow-md"
          style={{ backgroundColor: designColor }}
          title={artifact.designationName1}
        />
      )}
    </div>
  )
}
