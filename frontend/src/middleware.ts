import { withAuth } from 'next-auth/middleware'
import { NextResponse } from 'next/server'

export default withAuth(
  function middleware(req) {
    return NextResponse.next()
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
  }
)

// Protect all routes except auth pages and public assets
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/scan/:path*',
    '/billing/:path*',
    '/settings/:path*',
    '/report/:path*',
  ],
}
