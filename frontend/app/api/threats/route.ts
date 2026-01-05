import { NextResponse } from 'next/server'

export async function GET() {
  const mockThreats = [
    {
      id: '1',
      type: 'Deepfake Detection',
      severity: 'high',
      description: 'Potential deepfake video detected in transaction stream',
      timestamp: new Date().toISOString()
    },
    {
      id: '2',
      type: 'Voice Spoofing',
      severity: 'medium',
      description: 'Abnormal vocal patterns detected',
      timestamp: new Date().toISOString()
    }
  ]
  return NextResponse.json(mockThreats)
}