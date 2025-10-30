/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable HTTPS support for development
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  // Allow external origins for development
  allowedDevOrigins: [
    'localhost:3000',
    '127.0.0.1:3000',
    '192.168.10.210:3000',
    '192.168.10.244:3000',
    '0.0.0.0:3000'
  ],
  // Configure webpack for HTTPS development
  webpack(config) {
    // Add any necessary webpack configurations for HTTPS
    return config;
  }
};

module.exports = nextConfig;