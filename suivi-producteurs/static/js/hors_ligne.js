/* Saisie hors ligne des producteurs.
   Une fiche envoyée sans réseau est gardée sur le téléphone (localStorage), puis envoyée
   automatiquement dès que le réseau revient (ou à la prochaine ouverture de l'application). */
(function () {
  "use strict";
  var CLE = "ciaf-fiches-en-attente";
  var CLE_ECHECS = "ciaf-fiches-a-verifier";

  function lire(cle) {
    try { return JSON.parse(localStorage.getItem(cle) || "[]"); } catch (e) { return []; }
  }
  function ecrire(cle, liste) {
    try { localStorage.setItem(cle, JSON.stringify(liste)); return true; } catch (e) { return false; }
  }
  function semaineDe(url) {
    var m = /\/saisie\/(\d{4}-\d{2}-\d{2})\//.exec(url);
    if (!m) return "";
    var p = m[1].split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }

  /* ---- bandeau d'information en haut de la page ---- */
  function bandeau(texte, classe) {
    var zone = document.querySelector("main .wrap");
    if (!zone) return;
    var ancien = document.getElementById("bandeau-hors-ligne");
    if (ancien) ancien.remove();
    if (!texte) return;
    var div = document.createElement("div");
    div.id = "bandeau-hors-ligne";
    div.className = "notice " + (classe || "warn");
    div.setAttribute("role", "status");
    div.innerHTML = texte;
    zone.insertBefore(div, zone.firstChild);
  }

  function afficherEtat() {
    var attente = lire(CLE), echecs = lire(CLE_ECHECS);
    var morceaux = [];
    if (attente.length) {
      morceaux.push("<b>📶 " + attente.length + " fiche" + (attente.length > 1 ? "s" : "") +
        " en attente d'envoi</b> (semaine du " + attente.map(function (f) { return semaineDe(f.url); }).join(", ") +
        "). Elle" + (attente.length > 1 ? "s seront envoyées" : " sera envoyée") +
        " automatiquement dès que le téléphone aura du réseau. Ne vous déconnectez pas.");
    }
    if (echecs.length) {
      morceaux.push("<b>⚠️ À vérifier :</b> la fiche de la semaine du " +
        echecs.map(function (f) { return semaineDe(f.url); }).join(", ") +
        " n'a pas pu être enregistrée (elle a peut-être déjà été validée). Ouvrez-la pour vérifier.");
    }
    bandeau(morceaux.join("<br>"), echecs.length ? "warn" : "info");
  }

  /* ---- envoi au serveur ---- */
  function envoyer(item) {
    var ctrl = window.AbortController ? new AbortController() : null;
    var minuterie = setTimeout(function () { if (ctrl) ctrl.abort(); }, 20000);
    return fetch(item.url, {
      method: "POST",
      body: new URLSearchParams(item.donnees),
      credentials: "same-origin",
      redirect: "follow",
      signal: ctrl ? ctrl.signal : undefined
    }).then(function (rep) {
      clearTimeout(minuterie);
      return rep.text().then(function (html) {
        // Fiche enregistrée : le serveur renvoie vers l'accueil.
        var ok = rep.redirected && new URL(rep.url).pathname === "/";
        return { ok: ok, html: html, url: rep.url };
      });
    }, function (err) { clearTimeout(minuterie); throw err; });
  }

  var envoiEnCours = false;
  function viderFile() {
    if (envoiEnCours || !navigator.onLine) return;
    var attente = lire(CLE);
    if (!attente.length) return;
    envoiEnCours = true;
    var envoyees = 0;
    (function suivant() {
      var file = lire(CLE);
      if (!file.length) {
        envoiEnCours = false;
        if (envoyees) {
          try { sessionStorage.setItem("ciaf-envoyees", String(envoyees)); } catch (e) { /* rien */ }
          // On recharge la page pour afficher la fiche telle que le serveur l'a enregistrée.
          if (location.pathname === "/" || /^\/saisie\//.test(location.pathname)) { location.reload(); return; }
        }
        afficherEtat();
        return;
      }
      var item = file[0];
      envoyer(item).then(function (res) {
        file = lire(CLE);
        file.shift();
        ecrire(CLE, file);
        if (res.ok) envoyees += 1;
        else { var e = lire(CLE_ECHECS); e.push(item); ecrire(CLE_ECHECS, e); }
        suivant();
      }, function () {
        envoiEnCours = false;  // toujours pas de réseau : on réessaiera plus tard
        afficherEtat();
      });
    })();
  }

  /* ---- formulaire de saisie ---- */
  var form = document.getElementById("fiche");
  if (form) {
    // Une fiche en attente pour cette semaine ? On remet ses chiffres dans le formulaire.
    var enAttente = lire(CLE).filter(function (f) { return f.url === form.action || f.url === location.href; }).pop();
    if (enAttente) {
      enAttente.donnees.forEach(function (paire) {
        if (paire[0] === "csrfmiddlewaretoken") return;
        var champ = form.elements[paire[0]];
        if (champ) champ.value = paire[1];
      });
      form.dispatchEvent(new Event("input", { bubbles: true }));
    }
    // Ouvrir la fiche efface l'avertissement « à vérifier » la concernant.
    ecrire(CLE_ECHECS, lire(CLE_ECHECS).filter(function (f) { return f.url !== location.href; }));

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var bouton = document.querySelector('button[form="fiche"]');
      if (bouton) { bouton.disabled = true; bouton.textContent = "Envoi en cours…"; }
      var item = { url: form.action || location.href, donnees: Array.from(new FormData(form).entries()),
                   quand: new Date().toISOString() };
      envoyer(item).then(function (res) {
        // Réponse du serveur (accueil ou fiche avec erreurs) : on l'affiche telle quelle.
        ecrire(CLE, lire(CLE).filter(function (f) { return f.url !== item.url; }));
        document.open();
        document.write(res.html);
        document.close();
        history.replaceState(null, "", res.url);
      }, function () {
        // Pas de réseau : la fiche est gardée sur le téléphone.
        var file = lire(CLE).filter(function (f) { return f.url !== item.url; });
        file.push(item);
        if (!ecrire(CLE, file)) {
          bandeau("Pas de réseau, et le téléphone n'a pas pu garder la fiche. Réessayez quand vous aurez du réseau.", "warn");
          if (bouton) { bouton.disabled = false; bouton.textContent = "Envoyer ma fiche"; }
          return;
        }
        if (bouton) { bouton.disabled = false; bouton.textContent = "Envoyer ma fiche"; }
        window.scrollTo(0, 0);
        bandeau("<b>📶 Pas de réseau : votre fiche est gardée sur le téléphone.</b><br>" +
          "Elle sera envoyée automatiquement dès que vous aurez du réseau. Vous pouvez fermer l'application.", "warn");
      });
    });
  }

  /* ---- déconnexion : on prévient s'il reste des fiches non envoyées ---- */
  document.querySelectorAll('form[action$="/deconnexion/"]').forEach(function (f) {
    f.addEventListener("submit", function (ev) {
      if (lire(CLE).length && !window.confirm("Une fiche n'est pas encore envoyée. Si vous vous déconnectez, elle sera perdue. Continuer ?")) {
        ev.preventDefault();
        return;
      }
      ecrire(CLE, []);
      ecrire(CLE_ECHECS, []);
      if (navigator.serviceWorker && navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage("vider-pages");
    });
  });

  /* ---- accueil : on prépare la fiche de la semaine pour l'utiliser sans réseau ---- */
  if (navigator.onLine && location.pathname === "/") {
    Array.prototype.slice.call(document.querySelectorAll('a[href^="/saisie/"]'), 0, 3).forEach(function (a) {
      fetch(a.href, { credentials: "same-origin" }).catch(function () {});
    });
  }

  window.addEventListener("online", viderFile);
  window.addEventListener("offline", function () {
    if (!lire(CLE).length) bandeau("📶 Pas de réseau. Vous pouvez quand même remplir votre fiche : elle sera envoyée plus tard.", "info");
  });
  afficherEtat();
  var dejaEnvoyees = null;
  try { dejaEnvoyees = sessionStorage.getItem("ciaf-envoyees"); sessionStorage.removeItem("ciaf-envoyees"); } catch (e) { /* rien */ }
  if (dejaEnvoyees) bandeau("<b>✅ " + dejaEnvoyees + " fiche" + (dejaEnvoyees > 1 ? "s envoyées" : " envoyée") +
    "</b> : le réseau est revenu, votre fiche a été transmise à votre responsable.", "info");
  viderFile();
})();
