const CACHE_NAME = "spielpendium-cache-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/collection",
  "/statistics",
  "/settings",
  "/assets/style.css",
  "/assets/logo-192.png",
  "/assets/logo-512.png",
  "/assets/powered-by-bgg-rgb.png",
  "/assets/powered-by-bgg-rgb.svg",
  "/assets/powered-by-bgg-reversed-rgb.svg",
  "/assets/sliderLabels.js"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  // Only handle GET requests and local origin requests
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  const isStatic = url.pathname.startsWith("/assets/") ||
                   url.pathname.startsWith("/_dash-component-suites/") ||
                   url.pathname.startsWith("/_dash-layout") ||
                   url.pathname.startsWith("/_dash-dependencies");

  if (isStatic) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) {
          // Fetch update in background for next time
          fetch(event.request).then(networkResponse => {
            if (networkResponse.status === 200) {
              caches.open(CACHE_NAME).then(cache => cache.put(event.request, networkResponse));
            }
          }).catch(() => {});
          return cachedResponse;
        }
        return fetch(event.request).then(networkResponse => {
          if (networkResponse.status === 200) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return networkResponse;
        });
      })
    );
  } else {
    // Network first for dynamic routes and other endpoints
    event.respondWith(
      fetch(event.request).then(networkResponse => {
        if (networkResponse.status === 200) {
          const clone = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return networkResponse;
      }).catch(() => {
        return caches.match(event.request);
      })
    );
  }
});
