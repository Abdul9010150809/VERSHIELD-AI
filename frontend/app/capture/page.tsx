'use client'

import { useState, useRef } from 'react'
import { Card, Button, Text, Title } from '@tremor/react'

type ValidationStep = 'initial' | 'confirmation' | 'complete'

export default function CapturePage() {
  const [isRecording, setIsRecording] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [diffDetails, setDiffDetails] = useState<string[]>([])
  const [analysis, setAnalysis] = useState<{
    vision_score?: number
    acoustic_score?: number
    mismatches?: string[]
    reasoning?: string
    decision?: string
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [validationStep, setValidationStep] = useState<ValidationStep>('initial')
  const [firstCaptureData, setFirstCaptureData] = useState<{video: string, audio: string} | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      })

      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }

      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' })
        await analyzeMedia(blob)
      }

      mediaRecorder.start()
      setIsRecording(true)
      setResult(null)
      setAnalysis(null)

      // Auto-stop after 5 seconds for demo
      setTimeout(() => {
        stopCapture()
      }, 5000)

    } catch (error) {
      console.error('Error accessing media devices:', error)
      alert('Unable to access camera and microphone. Please check permissions.')
    }
  }

  const stopCapture = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }

    setIsRecording(false)
  }

  const analyzeMedia = async (blob: Blob) => {
    setLoading(true)
    setResult(null)
    try {
      // Convert blob to base64
      const videoB64 = await blobToBase64(blob)
      const audioB64 = videoB64 // For demo, using same data

      // Two-step validation process
      if (validationStep === 'initial') {
        // Store first capture for comparison
        setFirstCaptureData({ video: videoB64, audio: audioB64 })
        setResult('✅ First capture stored. Please record a second sample within 30 seconds.')
        setDiffDetails([])
        setAnalysis(null)
        setValidationStep('confirmation')
        setLoading(false)
        return
      }

      console.log('Sending TWO-STEP validation to /api/analyze...')
      
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_b64: videoB64,
          audio_b64: audioB64,
          first_capture: firstCaptureData, // Include first capture for comparison
          validation_step: 'confirmation',
          metadata: { 
            timestamp: new Date().toISOString(),
            two_step_validation: true 
          },
          transaction_amount: 100.00
        }),
      })

      console.log('Response status:', response.status)
      
      if (!response.ok) {
        const errorData = await response.json()
        console.error('Backend error:', errorData)
        setResult(`Error: ${errorData.error || response.statusText}`)
        return
      }

      const data = await response.json()
      console.log('Two-step validation result:', data)

      // Build simple diff between first and second captures
      const deltas: string[] = []
      if (firstCaptureData) {
        const videoDelta = Math.abs((firstCaptureData.video?.length || 0) - videoB64.length)
        const audioDelta = Math.abs((firstCaptureData.audio?.length || 0) - audioB64.length)
        const pct = (delta: number, base: number) => base === 0 ? 0 : Math.round((delta / base) * 100)

        if (videoDelta > 500) {
          deltas.push(`Video sample size differs by ~${pct(videoDelta, firstCaptureData.video.length)}% (possible different framing or feed)`)
        }
        if (audioDelta > 500) {
          deltas.push(`Audio sample size differs by ~${pct(audioDelta, firstCaptureData.audio.length)}% (possible different speaker/noise)`)
        }
        if (deltas.length === 0) {
          deltas.push('No significant size differences detected between captures (basic consistency check passed).')
        }
      }

      setDiffDetails(data.mismatches || deltas)
      setAnalysis({
        vision_score: data.vision_score,
        acoustic_score: data.acoustic_score,
        mismatches: data.mismatches,
        reasoning: data.reasoning,
        decision: data.decision,
      })

      // Mark validation as complete
      setValidationStep('complete')

      if (data.decision === 'authorized') {
        setResult('✅ AUTHORIZED - Two-step biometric verification passed. Captures aligned with liveness checks.')
      } else if (data.decision === 'not authorized') {
        setResult('❌ NOT AUTHORIZED - Verification failed. Captures did not align or spoofing risk detected.')
      } else {
        setResult(`Result: ${JSON.stringify(data)}`)
      }

    } catch (error) {
      console.error('Analysis error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      setResult(`Error: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const resetValidation = () => {
    setValidationStep('initial')
    setFirstCaptureData(null)
    setResult(null)
    setDiffDetails([])
    setAnalysis(null)
    setLoading(false)
  }

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        // Remove the data URL prefix
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Title className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            VeriShield AI - Two-Step Verification
          </Title>
          <Text className="text-gray-600 mt-2">
            Two-step biometric validation: Capture twice for enhanced security and liveness detection
          </Text>
          <div className="mt-4 flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
              validationStep === 'initial' ? 'bg-blue-100 text-blue-700' : 
              validationStep === 'confirmation' ? 'bg-yellow-100 text-yellow-700' : 
              'bg-green-100 text-green-700'
            }`}>
              <span className="font-semibold">Step {validationStep === 'initial' ? '1' : validationStep === 'confirmation' ? '2' : '✓'}</span>
              <span className="text-sm">
                {validationStep === 'initial' ? 'Initial Capture' : 
                 validationStep === 'confirmation' ? 'Confirmation Capture' : 
                 'Validated'}
              </span>
            </div>
            {(validationStep === 'confirmation' || validationStep === 'complete') && (
              <Button
                onClick={resetValidation}
                variant="secondary"
                size="xs"
              >
                Reset
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Video Capture */}
          <Card className="bg-white shadow-xl rounded-2xl border-0 overflow-hidden">
            <div className="p-6">
              <Title className="text-xl font-bold mb-4">Live Capture</Title>

              <div className="relative bg-gray-900 rounded-lg overflow-hidden mb-4">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  className={`w-full h-64 object-cover ${isRecording ? 'video-visible' : 'video-hidden'}`}
                />
                {!isRecording && (
                  <div className="absolute inset-0 flex items-center justify-center text-white">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mb-4 mx-auto">
                        📹
                      </div>
                      <p>Click "Start Capture" to begin</p>
                    </div>
                  </div>
                )}

                {isRecording && (
                  <div className="absolute top-4 right-4">
                    <div className="flex items-center space-x-2 bg-red-500 text-white px-3 py-1 rounded-full">
                      <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium">Recording</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex space-x-4">
                {!isRecording ? (
                  <Button
                    onClick={startCapture}
                    disabled={validationStep === 'complete'}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {validationStep === 'initial' ? 'Start First Capture' : 
                     validationStep === 'confirmation' ? 'Start Second Capture' : 
                     'Validation Complete'}
                  </Button>
                ) : (
                  <Button
                    onClick={stopCapture}
                    className="flex-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200"
                  >
                    Stop & {validationStep === 'initial' ? 'Store' : 'Validate'}
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* Results */}
          <Card className="bg-white shadow-xl rounded-2xl border-0 overflow-hidden">
            <div className="p-6">
              <Title className="text-xl font-bold mb-4">Authorization Result</Title>

              {loading && (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  <span className="ml-4 text-gray-600">Analyzing...</span>
                </div>
              )}

              {result && !loading && (
                <div className={`p-6 rounded-lg border-2 ${
                  result.includes('AUTHORIZED')
                    ? 'bg-green-50 border-green-200'
                    : result.includes('Error')
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-start">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-4 flex-shrink-0 text-white ${
                      result.includes('AUTHORIZED')
                        ? 'bg-green-500'
                        : result.includes('Error')
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}>
                      {result.includes('AUTHORIZED') ? '✓' : result.includes('Error') ? '⚠' : '✗'}
                    </div>
                    <div className="flex-1">
                      <Text className={`font-bold text-lg ${
                        result.includes('AUTHORIZED')
                          ? 'text-green-700'
                          : result.includes('Error')
                          ? 'text-yellow-700'
                          : 'text-red-700'
                      }`}>
                        {result}
                      </Text>
                      <Text className="text-gray-700 text-sm mt-1">
                        {analysis?.reasoning || (result.includes('AUTHORIZED')
                          ? 'Biometric verification successful'
                          : result.includes('NOT AUTHORIZED')
                          ? 'Security check failed - transaction blocked'
                          : 'An error occurred during analysis')}
                      </Text>

                      {analysis && (
                        <div className="mt-4 grid gap-3">
                          <div>
                            <div className="flex items-center justify-between text-sm text-gray-700 mb-1">
                              <span className="font-semibold">Face liveness risk</span>
                              <span>{Math.round((analysis.vision_score ?? 0) * 100)}%</span>
                            </div>
                            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                              <div
                                className={`${(analysis.vision_score ?? 0) > 0.5 ? 'bg-red-500' : 'bg-green-500'} h-2 transition-all`}
                                style={{ width: `${Math.min(100, Math.max(0, Math.round((analysis.vision_score ?? 0) * 100)))}%` }}
                              />
                            </div>
                          </div>

                          <div>
                            <div className="flex items-center justify-between text-sm text-gray-700 mb-1">
                              <span className="font-semibold">Voice spoof risk</span>
                              <span>{Math.round((analysis.acoustic_score ?? 0) * 100)}%</span>
                            </div>
                            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                              <div
                                className={`${(analysis.acoustic_score ?? 0) > 0.6 ? 'bg-red-500' : 'bg-amber-500'} h-2 transition-all`}
                                style={{ width: `${Math.min(100, Math.max(0, Math.round((analysis.acoustic_score ?? 0) * 100)))}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {diffDetails.length > 0 && (
                        <div className="mt-3 space-y-1 text-sm text-gray-700">
                          <p className="font-semibold text-gray-800">Capture comparison:</p>
                          {diffDetails.map((item, idx) => (
                            <p key={idx} className="flex items-start space-x-2">
                              <span className="mt-1 text-gray-400">•</span>
                              <span>{item}</span>
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {!result && !loading && (
                <div className="text-center py-12 text-gray-500">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4 mx-auto">
                    🔒
                  </div>
                  <p>Start capture to check authorization</p>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="mt-8 text-center">
          <Text className="text-gray-500 text-sm">
            🔒 Two-step validation: Each capture is 5 seconds. The second capture validates against the first for enhanced security.
            This prevents replay attacks and ensures live presence.
          </Text>
        </div>
      </div>
    </div>
  )
}