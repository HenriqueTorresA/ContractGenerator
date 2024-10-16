var staticCacheName = 'djangopwa-v1';
 
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(staticCacheName).then(function(cache) {
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
  var requestUrl = new URL(event.request.url);
    if (requestUrl.origin === location.origin) {
      if ((requestUrl.pathname === '/')) {
        event.respondWith(caches.match('/home'));
        return;
      }
    }
    event.respondWith(
      caches.match(event.request).then(function(response) {
        return response || fetch(event.request);
      })
    );
});


let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevenir que o Chrome mostre automaticamente o prompt
  e.preventDefault();
  // Salvar o evento para ser usado mais tarde
  deferredPrompt = e;
  // Aqui você pode exibir o botão de "instalar" de forma personalizada
  showInstallButton();
});

const installButton = document.getElementById('installButton');

installButton.addEventListener('click', (e) => {
  // Mostrar o prompt de instalação
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('Usuário aceitou o prompt de instalação');
    } else {
      console.log('O usuário ignorou o prompt de instalação');
    }
    deferredPrompt = null;
  });
});
