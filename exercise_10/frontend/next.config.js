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
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8600';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  // Allow external origins for development
  allowedDevOrigins: [
    'localhost:8501',
    '127.0.0.1:8501',
    '192.168.10.210:8501',
    '192.168.10.244:8501',
    '0.0.0.0:8501',
    '103.98.213.149:8501'
  ],
  // Configure webpack for HTTPS development
  webpack(config) {
    // Add any necessary webpack configurations for HTTPS
    return config;
  }
};

module.exports = nextConfig;