import { NextRequest, NextResponse } from 'next/server'
import { fetchRelicList, normalizeArtifactImages } from '@/lib/emuseum'

export async function GET(req: NextRequest) {
  const serviceKey = process.env.EMUSEUM_SERVICE_KEY
  if (!serviceKey) {
    return NextResponse.json({ error: 'API key not configured' }, { status: 500 })
  }

  const { searchParams } = req.nextUrl
  const params = {
    serviceKey,
    numOfRows: Number(searchParams.get('numOfRows') || 50),
    pageNo: Number(searchParams.get('pageNo') || 1),
    name: searchParams.get('name') || undefined,
    nameKr: searchParams.get('nameKr') || undefined,
    nationalityCode: searchParams.get('nationalityCode') || undefined,
    materialCode: searchParams.get('materialCode') || undefined,
    purposeCode: searchParams.get('purposeCode') || undefined,
    placeLandCode: searchParams.get('placeLandCode') || undefined,
    designationCode: searchParams.get('designationCode') || undefined,
    museumCode: searchParams.get('museumCode') || undefined,
    indexWord: searchParams.get('indexWord') || undefined,
  }

  try {
    const data = await fetchRelicList(params)
    // 이미지 URL 정규화
    if (data.list) {
      data.list = data.list.map(normalizeArtifactImages)
    }
    return NextResponse.json(data)
  } catch (error) {
    console.error('eMuseum API error:', error)
    return NextResponse.json({ error: 'Failed to fetch artifacts' }, { status: 502 })
  }
}
