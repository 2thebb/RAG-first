import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '한국 유물 지도 | Korea Artifact Map',
  description: '이뮤지엄 소장품을 한반도 지도 위에 시각화합니다',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-[#080e1a] text-[#e8dcc8] h-screen overflow-hidden">{children}</body>
    </html>
  )
}
