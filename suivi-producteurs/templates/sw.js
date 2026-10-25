/* Service worker : application installable et utilisable sans réseau par les producteurs.
   - fichiers de style et scripts : gardés sur le téléphone ;
   - pages du producteur (accueil et fiches) : réseau d'abord, sinon la dernière version gardée ;
   - l'envoi d'une fiche sans réseau est mis en attente par static/js/hors_ligne.js. */
const STATIQUE = "ciaf-statique-v4";
const PAGES = "ciaf-pages-v1";
const A_GARDER = ["/static/css/app.css", "/static/js/saisie.js", "/static/js/hors_ligne.js"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(STATIQUE).then((c) => c.addAll(A_GARDER)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== STATIQUE && k !== PAGES).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("message", (e) => {
  if (e.data === "vider-pages") caches.delete(PAGES);  // à la déconnexion
});

function pageProducteur(url) {
  return url.pathname === "/" || url.pathname.startsWith("/saisie/");
}

function delai(ms) {
  return new Promise((_, refus) => setTimeout(() => refus(new Error("délai")), ms));
}

const PAGE_HORS_LIGNE = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Pas de réseau</title>
<link rel="stylesheet" href="/static/css/app.css"></head><body class="mobile"><main><div class="wrap">
<div class="card connexion"><h1>Pas de réseau</h1>
<p>Cette page n'a pas encore été ouverte sur ce téléphone avec du réseau, elle n'est donc pas disponible hors ligne.</p>
<p class="muted">Revenez à l'accueil : la fiche de la semaine y est disponible si vous l'avez déjà ouverte une fois avec du réseau.</p>
<a class="btn primary big" href="/">Retour à l'accueil</a></div></div></main></body></html>`;

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/static/") || url.pathname.startsWith("/media/logo/")) {
    e.respondWith(caches.match(req).then((r) => r || fetch(req).then((rep) => {
      if (rep.ok) caches.open(STATIQUE).then((c) => c.put(req, rep.clone()));
      return rep;
    })));
    return;
  }

  if (pageProducteur(url)) {
    e.respondWith(
      Promise.race([fetch(req), delai(10000)]).then((rep) => {
        // On ne garde que les vraies pages du producteur (pas la page de connexion après une redirection).
        if (rep.ok && !rep.redirected) caches.open(PAGES).then((c) => c.put(req, rep.clone()));
        return rep;
      }).catch(() => caches.match(req, { ignoreSearch: true }).then((r) => r ||
        new Response(PAGE_HORS_LIGNE, { headers: { "Content-Type": "text/html; charset=utf-8" } })))
    );
  }
});
