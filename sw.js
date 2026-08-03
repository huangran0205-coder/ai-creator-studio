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

// 处理 Web Share Target 分享：拦截 POST 请求（兼容旧缓存）
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // 拦截 POST 请求到 share-receiver（GitHub Pages 不支持 POST）
  if (event.request.method === 'POST' && url.pathname.includes('share-receiver')) {
    event.respondWith(
      event.request.formData().then(formData => {
        const sharedUrl = formData.get('url') || formData.get('text') || '';
        // 转为 GET 请求，通过 query 参数传递
        return Response.redirect('./share-receiver.html?url=' + encodeURIComponent(sharedUrl), 303);
      }).catch(() => {
        return Response.redirect('./share-receiver.html', 303);
      })
    );
    return;
  }

  // 普通缓存策略
  event.respondWith(
    caches.match(event.request).then(res =>
      res || fetch(event.request).catch(() => new Response('离线模式', { status: 200 }))
    )
  );
});