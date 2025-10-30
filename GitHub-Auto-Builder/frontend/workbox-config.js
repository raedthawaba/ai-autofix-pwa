/**
 * Workbox Configuration for AI Auto-Fix PWA
 * Optimizes caching and offline functionality
 */

module.exports = {
  // Glob patterns to precache
  globDirectory: 'build/',
  globPatterns: [
    '**/*.{js,css,html,png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot}',
    'manifest.json',
    'offline.html',
    'icons/**/*',
    'sw.js'
  ],
  
  // Swapping strategies
  navigateFallback: 'offline.html',
  
  // Runtime caching rules
  runtimeCaching: [
    {
      // GitHub API
      urlPattern: /^https:\/\/api\.github\.com\//,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'github-api-cache',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 5 * 60 // 5 minutes
        },
        cacheableResponse: {
          statuses: [0, 200]
        }
      }
    },
    
    {
      // App API endpoints
      urlPattern: /\/api\//,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 2 * 60 // 2 minutes
        },
        cacheableResponse: {
          statuses: [0, 200, 201, 204]
        }
      }
    },
    
    {
      // Static assets
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'images-cache',
        expiration: {
          maxEntries: 60,
          maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
        },
        cacheableResponse: {
          statuses: [0, 200]
        }
      }
    },
    
    {
      // Fonts
      urlPattern: /\.(?:woff|woff2|ttf|eot)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'fonts-cache',
        expiration: {
          maxEntries: 20,
          maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
        },
        cacheableResponse: {
          statuses: [0, 200]
        }
      }
    },
    
    {
      // CSS and JS
      urlPattern: /\.(?:js|css)$/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'static-resources',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 7 * 24 * 60 * 60 // 7 days
        },
        cacheableResponse: {
          statuses: [0, 200]
        }
      }
    }
  ],
  
  // Skip waiting and clients claim for immediate updates
  skipWaiting: true,
  clientsClaim: true,
  
  // Directory to place generated files
  swSrc: 'public/sw.js',
  
  // Navigation preload
  navigationPreload: true,
  
  // Clean up outdated caches
  cleanupOutdatedCaches: true,
  
  // Maximum file size to precache (in bytes)
  maximumFileSizeToCacheInBytes: 3 * 1024 * 1024, // 3MB
  
  // Custom precache manifest filename
  precacheManifestFilename: 'workbox-precache-manifest.[manifestHash].js',
  
  // Additional Workbox options
  dontCacheBustURLsMatching: /\.\w{8}\./,
  
  // Offline fallback
  offlineGoogleAnalytics: false
};