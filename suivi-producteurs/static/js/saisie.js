/* Saisie mobile : ajout d'un produit depuis la liste du secteur, et total des valeurs en direct. */
(function () {
  const fmt = new Intl.NumberFormat("fr-FR");
  document.querySelectorAll("[data-jeu]").forEach(function (carte) {
    const nom = carte.dataset.jeu;
    const total = carte.querySelector('input[name="' + nom + '-TOTAL_FORMS"]');
    const modele = carte.querySelector("template");
    const choix = carte.querySelector("[data-ajouter]");
    choix.addEventListener("change", function () {
      const valeur = choix.value;
      if (!valeur) return;
      const option = choix.selectedOptions[0];
      const i = parseInt(total.value, 10);
      carte.querySelector(".lignes").insertAdjacentHTML("beforeend", modele.innerHTML.replace(/__prefix__/g, String(i)));
      total.value = i + 1;
      const ligne = carte.querySelector(".lignes .ligne:last-child");
      const libelle = ligne.querySelector('input[name$="-libelle"]');
      const chiffre = ligne.querySelector('input[type="number"]');
      if (valeur === "__autre__") {
        libelle.focus();
      } else {
        libelle.value = valeur;
        const unite = option.dataset.unite;
        const etiquette = ligne.querySelector("[data-unite]");
        if (unite && etiquette) etiquette.textContent = "Nombre (" + unite + ")";
        chiffre.focus();
      }
      choix.value = "";
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
