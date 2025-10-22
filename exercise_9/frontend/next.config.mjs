/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Use a custom dist directory to avoid potential Windows file locking on .next
  distDir: 'build',
  // Tweak watch options for Windows/PowerShell environments to reduce file access contention
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

export default nextConfig;

