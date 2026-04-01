// static/sw.js - v2 (обновлённый)
const CACHE_NAME = 'flet-kislorod-v2';  // ✅ Увеличил версию
const ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/sw.js',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();  // ✅ Активируем сразу
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => 
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();  // ✅ Берём контроль сразу
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => 
      response || fetch(e.request)
    )
  );
});