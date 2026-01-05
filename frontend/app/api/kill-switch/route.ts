import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json()
  // Mock handling
  return NextResponse.json({ success: true, active: body.active })
}