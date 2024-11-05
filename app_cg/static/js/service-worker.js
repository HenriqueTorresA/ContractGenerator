self.addEventListener('install', function(event) {
  console.log('Service Worker instalado');
  event.waitUntil(
    caches.open(staticCacheName).then(function(cache) {
      console.log('Abrindo cache e adicionando arquivos');
      return cache.addAll([
        '/',
        '/home',
        '/tela-de-negociacao/',
        '/resumo-do-contrato/',
      ]);
    })
  );
});

self.addEventListener('fetch', function(event) {
  console.log('Fetch para:', event.request.url);
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});
