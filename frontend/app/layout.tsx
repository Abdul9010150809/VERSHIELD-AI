import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'VeriShield AI - Deepfake Detection',
  description: 'Real-time deepfake detection and threat response system with two-step biometric validation',
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
