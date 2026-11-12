// Netz zuerst; bei fehlendem Netz die zuletzt geladene Version (die App funktioniert auch offline)
const C = 'dts-v2';
const PRE = ["./", "dialogs.html", "manifest.webmanifest", "icon-192.png", "history.json", "logo.png", "vfc-logo.png", "spieler/juliano-goncalves-da-costa.png", "spieler/kevin-notter.png", "spieler/nevio-bachmann.png", "spieler/tobias-fiedler.png"];
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(C).then(c => Promise.all(PRE.map(u => c.add(u).catch(() => {})))));
});
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const c = r.clone(); caches.open(C).then(x => x.put(e.request, c)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || (e.request.mode === 'navigate' ? caches.match('./') : undefined))));
});
