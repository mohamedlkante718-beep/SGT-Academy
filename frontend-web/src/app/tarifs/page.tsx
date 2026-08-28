import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Tarifs",
  description: "Les formules SGT Academy : formation individuelle, pack, entreprise.",
};

const PLANS = [
  {
    name: "Formation individuelle",
    description: "Achetez une formation à l'unité, accès immédiat après paiement.",
    cta: "Explorer le catalogue",
    href: "/formations",
  },
  {
    name: "Pack de formations",
    description: "Plusieurs formations liées à un même domaine (ex : parcours technicien SIG).",
    cta: "Bientôt disponible",
    href: "/formations",
  },
  {
    name: "Entreprise",
    description: "Licences en volume pour former votre équipe, avec suivi des progressions.",
    cta: "Nous contacter",
    href: "/contact",
  },
];

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-foreground">Tarifs</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Chaque formation a son propre prix, affiché sur sa page. Voici les formules disponibles.
      </p>

      <div className="mt-10 grid gap-6 sm:grid-cols-3">
        {PLANS.map((plan) => (
          <div key={plan.name} className="flex flex-col rounded-xl border border-border bg-white p-6">
            <h2 className="text-lg font-semibold text-foreground">{plan.name}</h2>
            <p className="mt-2 flex-1 text-sm text-muted">{plan.description}</p>
            <Link
              href={plan.href}
              className="mt-6 rounded-lg bg-brand px-4 py-2 text-center text-sm font-semibold text-white transition hover:bg-brand-dark"
            >
              {plan.cta}
            </Link>
          </div>
        ))}
      </div>

      <div className="mt-12 rounded-xl bg-brand-light p-8 text-center">
        <p className="text-lg font-semibold text-foreground">
          Besoin de former toute votre équipe ?
        </p>
        <Link href="/contact" className="mt-3 inline-block font-semibold text-brand hover:underline">
          Contactez-nous →
        </Link>
      </div>
    </div>
  );
}
