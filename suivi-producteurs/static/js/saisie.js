/* Saisie mobile : ajout de lignes et total des valeurs en direct. */
(function () {
  const fmt = new Intl.NumberFormat("fr-FR");
  document.querySelectorAll("[data-jeu]").forEach(function (carte) {
    const nom = carte.dataset.jeu;
    const total = carte.querySelector('input[name="' + nom + '-TOTAL_FORMS"]');
    const modele = carte.querySelector("template");
    carte.querySelector("[data-ajouter]").addEventListener("click", function () {
      const i = parseInt(total.value, 10);
      const html = modele.innerHTML.replace(/__prefix__/g, String(i));
      carte.querySelector(".lignes").insertAdjacentHTML("beforeend", html);
      total.value = i + 1;
      const champ = carte.querySelector(".lignes .ligne:last-child input[type=text]");
      if (champ) champ.focus();
    });
  });
  const sortie = document.getElementById("total");
  function maj() {
    let s = 0;
    document.querySelectorAll('[data-jeu="valeurs"] input[name$="-montant"]').forEach(function (el) {
      const v = parseFloat(el.value);
      if (isFinite(v)) s += v;
    });
    if (sortie) sortie.textContent = fmt.format(s) + " F";
  }
  maj();
  document.addEventListener("input", function (e) { if (e.target.name && e.target.name.endsWith("-montant")) maj(); });
})();
