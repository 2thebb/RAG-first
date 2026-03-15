/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'www.emuseum.go.kr',
        pathname: '/openapi/img/**',
      },
      {
        protocol: 'http',
        hostname: 'www.emuseum.go.kr',
        pathname: '/openapi/img/**',
      },
    ],
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [{ key: 'Cache-Control', value: 's-maxage=300, stale-while-revalidate' }],
      },
    ]
  },
}

module.exports = nextConfig
