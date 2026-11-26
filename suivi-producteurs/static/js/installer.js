/* Bouton « Installer l'application » : sur PC (Chrome, Edge) et Android, il ouvre la fenêtre
   d'installation du navigateur ; sur iPhone / iPad, il explique comment ajouter l'icône. */
(function () {
  "use strict";
  var bouton = document.getElementById("installer");
  if (!bouton) return;
  var dejaInstallee = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  if (dejaInstallee) return;
  var ios = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
            (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var demande = null;

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();          // on garde la demande pour notre bouton
    demande = e;
    bouton.hidden = false;
  });
  window.addEventListener("appinstalled", function () {
    bouton.hidden = true;
    demande = null;
  });
  if (ios) bouton.hidden = false;

  bouton.addEventListener("click", function () {
    if (demande) {
      demande.prompt();
      demande.userChoice.then(function () { demande = null; bouton.hidden = true; });
      return;
    }
    var aide = document.getElementById("aide-installation");
    if (aide) aide.hidden = !aide.hidden;
  });
})();
