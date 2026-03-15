import { NextRequest, NextResponse } from 'next/server'
import { fetchRelicDetail, normalizeArtifactImages } from '@/lib/emuseum'

export async function GET(req: NextRequest) {
  const serviceKey = process.env.EMUSEUM_SERVICE_KEY
  if (!serviceKey) {
    return NextResponse.json({ error: 'API key not configured' }, { status: 500 })
  }

  const id = req.nextUrl.searchParams.get('id')
  if (!id) {
    return NextResponse.json({ error: 'id is required' }, { status: 400 })
  }

  try {
    const data = await fetchRelicDetail(serviceKey, id)
    if (data.list) {
      data.list = data.list.map(normalizeArtifactImages)
    }
    return NextResponse.json(data)
  } catch (error) {
    console.error('eMuseum detail API error:', error)
    return NextResponse.json({ error: 'Failed to fetch artifact detail' }, { status: 502 })
  }
}
