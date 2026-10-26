/* Service worker : application installable et utilisable sans réseau par les producteurs.
   - fichiers de style et scripts : gardés sur le téléphone ;
   - pages du producteur (accueil et fiches) : réseau d'abord, sinon la dernière version gardée ;
   - l'envoi d'une fiche sans réseau est mis en attente par static/js/hors_ligne.js. */
const STATIQUE = "ciaf-statique-v5";
const PAGES = "ciaf-pages-v1";  // garder le même nom : les pages déjà gardées restent disponibles
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
<p>Le téléphone n'arrive pas à joindre le serveur, et cette page n'a pas encore été gardée sur le téléphone.</p>
<p class="muted">Rapprochez-vous d'un endroit avec du réseau puis touchez « Réessayer ». La première ouverture de l'application doit toujours se faire avec du réseau ; ensuite, l'accueil et la fiche de la semaine marchent sans réseau.</p>
<button class="btn primary big" type="button" onclick="location.reload()">Réessayer</button>
<a class="btn big" href="/">Retour à l'accueil</a></div></div></main></body></html>`;

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/static/") || url.pathname.startsWith("/media/logo/")) {
    e.respondWith(caches.match(req).then((r) => r || fetch(req).then((rep) => {
      if (rep.ok) { const copie = rep.clone(); caches.open(STATIQUE).then((c) => c.put(req, copie)); }
      return rep;
    })));
    return;
  }

  if (pageProducteur(url)) {
    e.respondWith(caches.match(req, { ignoreSearch: true }).then((gardee) => {
      const reseau = fetch(req).then((rep) => {
        // On ne garde que les vraies pages du producteur (pas la page de connexion après une redirection).
        // La copie doit être faite tout de suite, avant que le navigateur ne lise la page.
        if (rep.ok && !rep.redirected) { const copie = rep.clone(); caches.open(PAGES).then((c) => c.put(req, copie)); }
        return rep;
      });
      // Page déjà gardée : on attend le réseau 10 secondes au plus, puis on affiche la version gardée.
      // Page jamais gardée : on attend le réseau aussi longtemps qu'il le faut (réseau lent mais présent).
      const attente = gardee ? Promise.race([reseau, delai(10000)]) : reseau;
      return attente.catch(() => gardee ||
        new Response(PAGE_HORS_LIGNE, { headers: { "Content-Type": "text/html; charset=utf-8" } }));
    }));
  }
});
