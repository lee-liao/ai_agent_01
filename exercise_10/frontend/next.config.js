/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  // Allow all local network origins (safer for development)
  allowedDevOrigins: [
    // Match your specific client IP (check browser dev tools for exact origin)
    "192.168.10.244:3000",
    "http://192.168.10.244:3000",
    "ws://192.168.10.244:3000",
    // Allow any device on the 192.168.10.x subnet (common home network range)
    "192.168.10.:3000",
    "http://192.168.10.:3000", 
    "ws://192.168.10.:3000",
    // Fallback: allow localhost variants
    "localhost:3000",
    "http://localhost:3000",
    "ws://localhost:3000",
    "127.0.0.1:3000",
    "http://127.0.0.1:3000",
    "ws://127.0.0.1:3000",
  ],
  // Remove the webpack config - it's unnecessary for this issue
};

module.exports = nextConfig;