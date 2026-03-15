'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { Artifact } from '@/lib/types'

interface ProvinceData {
  name: string
  artifacts: Artifact[]
  count: number
}

interface KoreaMapProps {
  provinceArtifacts: Record<string, Artifact[]>
  selectedProvince: string | null
  onProvinceClick: (provinceName: string | null) => void
  loading?: boolean
}

const GEOJSON_URL =
  'https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea_provinces_2018_geo.json'

export default function KoreaMap({
  provinceArtifacts,
  selectedProvince,
  onProvinceClick,
  loading,
}: KoreaMapProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [geoData, setGeoData] = useState<GeoJSON.FeatureCollection | null>(null)
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null)

  useEffect(() => {
    fetch(GEOJSON_URL)
      .then((r) => r.json())
      .then(setGeoData)
      .catch(() => console.error('GeoJSON 로드 실패'))
  }, [])

  const drawMap = useCallback(() => {
    if (!geoData || !svgRef.current) return

    const container = svgRef.current.parentElement
    const width = container?.clientWidth || 480
    const height = container?.clientHeight || 600

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    svg.attr('width', width).attr('height', height)

    const projection = d3
      .geoMercator()
      .fitSize([width - 20, height - 20], geoData)
      .translate([width / 2, height / 2])

    const path = d3.geoPath().projection(projection)

    const defs = svg.append('defs')

    // 클립패스 + 이미지 패턴 정의
    geoData.features.forEach((feature: GeoJSON.Feature) => {
      const name = (feature.properties as Record<string, string>)?.['name'] || ''
      const artifacts = provinceArtifacts[name] || []
      if (artifacts.length === 0) return

      const clipId = `clip-${name.replace(/\s/g, '-')}`
      defs
        .append('clipPath')
        .attr('id', clipId)
        .append('path')
        .attr('d', path(feature as GeoJSON.Feature<GeoJSON.Geometry>) || '')
    })

    const g = svg.append('g')

    // 지도 배경 (바다)
    svg
      .insert('rect', 'g')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', '#0a1628')

    // 도별 그룹
    geoData.features.forEach((feature: GeoJSON.Feature) => {
      const props = feature.properties as Record<string, string>
      const name = props?.['name'] || ''
      const artifacts = provinceArtifacts[name] || []
      const count = artifacts.length
      const isSelected = selectedProvince === name

      const pathData = path(feature as GeoJSON.Feature<GeoJSON.Geometry>) || ''

      // 모자이크: 유물 이미지가 있으면 이미지로 채우기
      if (count > 0) {
        const clipId = `clip-${name.replace(/\s/g, '-')}`
        const patternId = `pattern-${name.replace(/\s/g, '-')}`

        // 경계 박스 계산
        const bounds = path.bounds(feature as GeoJSON.Feature<GeoJSON.Geometry>)
        const bw = bounds[1][0] - bounds[0][0]
        const bh = bounds[1][1] - bounds[0][1]
        const cellSize = Math.max(16, Math.min(36, Math.sqrt((bw * bh) / Math.max(count, 1))))

        const pattern = defs
          .append('pattern')
          .attr('id', patternId)
          .attr('x', bounds[0][0])
          .attr('y', bounds[0][1])
          .attr('width', cellSize)
          .attr('height', cellSize)
          .attr('patternUnits', 'userSpaceOnUse')

        // 썸네일 이미지 타일링
        const visibleArtifacts = artifacts.slice(0, 80)
        visibleArtifacts.forEach((art, i) => {
          const cols = Math.ceil(bw / cellSize)
          const row = Math.floor(i / cols)
          const col = i % cols
          if (art.imgThumUriS) {
            pattern
              .append('image')
              .attr('href', art.imgThumUriS)
              .attr('x', col * cellSize)
              .attr('y', row * cellSize)
              .attr('width', cellSize)
              .attr('height', cellSize)
              .attr('preserveAspectRatio', 'xMidYMid slice')
          }
        })

        // 이미지 모자이크 fill
        g.append('path')
          .attr('d', pathData)
          .attr('fill', `url(#${patternId})`)
          .attr('clip-path', `url(#${clipId})`)
          .attr('opacity', isSelected ? 1 : 0.85)

        // 선택 하이라이트
        g.append('path')
          .attr('d', pathData)
          .attr('fill', isSelected ? 'rgba(255,200,50,0.25)' : 'transparent')
          .attr('stroke', isSelected ? '#ffd700' : '#c8a96e')
          .attr('stroke-width', isSelected ? 3 : 1)
          .attr('cursor', 'pointer')
          .on('mouseenter', function (event) {
            d3.select(this).attr('fill', 'rgba(255,200,50,0.2)')
            setTooltip({ x: event.offsetX, y: event.offsetY, text: `${name} (${count}점)` })
          })
          .on('mousemove', function (event) {
            setTooltip({ x: event.offsetX, y: event.offsetY, text: `${name} (${count}점)` })
          })
          .on('mouseleave', function () {
            d3.select(this).attr('fill', isSelected ? 'rgba(255,200,50,0.25)' : 'transparent')
            setTooltip(null)
          })
          .on('click', () => onProvinceClick(isSelected ? null : name))
      } else {
        // 유물 없는 도: 단색
        g.append('path')
          .attr('d', pathData)
          .attr('fill', '#1e3050')
          .attr('stroke', '#2d4a6e')
          .attr('stroke-width', 0.8)
      }

      // 도 이름 라벨
      const centroid = path.centroid(feature as GeoJSON.Feature<GeoJSON.Geometry>)
      if (!isNaN(centroid[0])) {
        const shortName = name
          .replace('특별시', '')
          .replace('광역시', '')
          .replace('특별자치도', '')
          .replace('특별자치시', '')
          .replace('도', '')

        g.append('text')
          .attr('x', centroid[0])
          .attr('y', centroid[1])
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'middle')
          .attr('font-size', '9px')
          .attr('font-weight', '600')
          .attr('fill', count > 0 ? '#fff' : '#4a6080')
          .attr('pointer-events', 'none')
          .attr('text-shadow', '1px 1px 2px rgba(0,0,0,0.8)')
          .text(shortName)

        if (count > 0) {
          g.append('text')
            .attr('x', centroid[0])
            .attr('y', centroid[1] + 11)
            .attr('text-anchor', 'middle')
            .attr('font-size', '8px')
            .attr('fill', '#ffd700')
            .attr('pointer-events', 'none')
            .text(`${count}점`)
        }
      }
    })
  }, [geoData, provinceArtifacts, selectedProvince, onProvinceClick])

  useEffect(() => {
    drawMap()
  }, [drawMap])

  useEffect(() => {
    const handleResize = () => drawMap()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [drawMap])

  return (
    <div className="relative w-full h-full bg-[#0a1628] rounded-xl overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center z-10 bg-black/40">
          <div className="text-amber-300 text-sm animate-pulse">유물 로딩 중...</div>
        </div>
      )}
      <svg ref={svgRef} className="w-full h-full" />
      {tooltip && (
        <div
          className="absolute pointer-events-none bg-black/80 text-amber-200 text-xs px-2 py-1 rounded shadow-lg z-20"
          style={{ left: tooltip.x + 12, top: tooltip.y - 8 }}
        >
          {tooltip.text}
        </div>
      )}
      {!selectedProvince && (
        <div className="absolute bottom-3 left-3 text-xs text-slate-400">
          지도를 클릭하면 해당 지역 유물을 볼 수 있습니다
        </div>
      )}
    </div>
  )
}
