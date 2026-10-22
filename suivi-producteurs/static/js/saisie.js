/* Saisie mobile : total des valeurs mis à jour pendant la frappe. */
(function () {
  const sortie = document.getElementById("total");
  if (!sortie) return;
  const fmt = new Intl.NumberFormat("fr-FR");
  function maj() {
    let s = 0;
    document.querySelectorAll("input[data-valeur]").forEach(function (el) {
      const v = parseFloat(el.value);
      if (isFinite(v)) s += v;
    });
    sortie.textContent = fmt.format(s) + " F";
  }
  maj();
  document.addEventListener("input", function (e) { if (e.target.hasAttribute("data-valeur")) maj(); });
})();
