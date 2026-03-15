import { NextRequest, NextResponse } from 'next/server'
import { fetchCodes } from '@/lib/emuseum'

export async function GET(req: NextRequest) {
  const serviceKey = process.env.EMUSEUM_SERVICE_KEY
  if (!serviceKey) {
    return NextResponse.json({ error: 'API key not configured' }, { status: 500 })
  }

  const parentCode = req.nextUrl.searchParams.get('parentCode') || undefined

  try {
    const data = await fetchCodes(serviceKey, parentCode)
    return NextResponse.json(data)
  } catch (error) {
    console.error('eMuseum codes API error:', error)
    return NextResponse.json({ error: 'Failed to fetch codes' }, { status: 502 })
  }
}
