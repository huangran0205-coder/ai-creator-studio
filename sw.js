const CACHE = 'ai-creator-studio-v1';
const ASSETS = [
  'index.html',
  'manifest.json',
  'share-receiver.html'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// 处理 Web Share Target 分享（已改用 GET 方式，不需要额外处理）
self.addEventListener('fetch', event => {
  // 普通缓存策略
  event.respondWith(
    caches.match(event.request).then(res =>
      res || fetch(event.request).catch(() => new Response('离线模式', { status: 200 }))
    )
  );
});