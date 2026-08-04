const CACHE = 'ai-creator-studio-v3';
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

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // 放行跨域请求（API 调用等），让浏览器正常处理，不经过 SW 缓存
  if (url.origin !== self.location.origin) {
    return;
  }

  // 拦截 POST 请求到 share-receiver（GitHub Pages 不支持 POST）
  if (event.request.method === 'POST' && url.pathname.includes('share-receiver')) {
    event.respondWith(
      event.request.formData().then(formData => {
        const sharedUrl = formData.get('url') || formData.get('text') || '';
        return Response.redirect('./share-receiver.html?url=' + encodeURIComponent(sharedUrl), 303);
      }).catch(() => {
        return Response.redirect('./share-receiver.html', 303);
      })
    );
    return;
  }

  // 只缓存同源静态资源，失败时不返回假响应，让浏览器报真实错误
  if (['GET', 'HEAD'].includes(event.request.method)) {
    event.respondWith(
      caches.match(event.request).then(res => res || fetch(event.request))
    );
    return;
  }
});