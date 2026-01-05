import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { video_b64, audio_b64, metadata, transaction_amount, first_capture, validation_step } = body

    // In development, proxy to the backend
    // In production, this would call the Azure-deployed backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    const response = await fetch(`${backendUrl}/analyze/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_b64,
        audio_b64,
        metadata: metadata || {},
        transaction_amount: transaction_amount || 100.00,
        first_capture: first_capture || undefined,
        validation_step: validation_step || undefined
      }),
    })

    if (!response.ok) {
      const errText = await response.text()
      const message = `Backend error ${response.status}: ${errText || 'no body'}`
      console.error(message)
      return NextResponse.json({ error: message }, { status: response.status })
    }

    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Analysis failed' },
      { status: 500 }
    )
  }
}