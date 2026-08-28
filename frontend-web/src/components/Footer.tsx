import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-border bg-brand-light/60">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
          <div>
            <span className="text-lg font-semibold text-foreground">SGT Academy</span>
            <p className="mt-2 text-sm text-muted">
              Une plateforme de Safe Green Tech.
              <br />
              « Bâtissons un avenir meilleur »
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground">Plateforme</h3>
            <ul className="mt-3 space-y-2 text-sm text-muted">
              <li><Link href="/formations" className="hover:text-brand">Formations</Link></li>
              <li><Link href="/tarifs" className="hover:text-brand">Tarifs</Link></li>
              <li><Link href="/inscription" className="hover:text-brand">Créer un compte</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground">Support</h3>
            <ul className="mt-3 space-y-2 text-sm text-muted">
              <li><Link href="/contact" className="hover:text-brand">Contact</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground">Vérification</h3>
            <p className="mt-3 text-sm text-muted">
              Vérifiez l&apos;authenticité d&apos;un certificat SGT Academy sur la page dédiée
              en saisissant son code (ex : SGT-2026-QGIS-000125).
            </p>
          </div>
        </div>

        <p className="mt-10 text-xs text-muted">
          © {new Date().getFullYear()} Safe Green Tech — SGT Academy. Tous droits réservés.
        </p>
      </div>
    </footer>
  );
}
