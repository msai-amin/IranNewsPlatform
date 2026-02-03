import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Iran Situation Room',
  description: 'Real-time fact-checked intelligence from Iran',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <div className="flex items-center justify-between h-16">
              <a href="/" className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">ISR</span>
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-lg font-bold text-gray-900 leading-tight">Iran Situation Room</h1>
                  <p className="text-xs text-gray-500 leading-tight">Real-time verified intelligence</p>
                </div>
              </a>
              
              {/* Nav links */}
              <nav className="flex items-center gap-1">
                <a href="/" className="px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                  Latest
                </a>
                <a href="/?status=verified" className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                  Verified
                </a>
                <a href="/?status=unverified" className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                  Unverified
                </a>
                <a href="/dashboard" className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                  Dashboard
                </a>
              </nav>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 mt-16 bg-white">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-red-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xs">ISR</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Iran Situation Room</p>
                  <p className="text-xs text-gray-500">Automated intelligence pipeline</p>
                </div>
              </div>
              <p className="text-xs text-gray-400 text-center sm:text-right">
                Sources cross-referenced with BBC, Reuters, AP & trusted outlets
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
