import { NextResponse } from 'next/server'

export async function GET() {
  const mockMetrics = {
    authenticityScore: 95,
    falsePositiveRate: 2,
    processingSpeed: 150,
    totalAnalyzed: 10000
  }
  return NextResponse.json(mockMetrics)
}