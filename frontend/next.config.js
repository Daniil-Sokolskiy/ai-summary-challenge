/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone-сборка: в образ уезжает только server.js + минимальный
  // node_modules, без dev-зависимостей.
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
}

module.exports = nextConfig
