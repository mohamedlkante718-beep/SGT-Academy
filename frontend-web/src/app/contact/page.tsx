import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact",
  description: "Contactez Safe Green Tech pour toute question sur SGT Academy.",
};

// TODO (Safe Green Tech) : remplacer ces coordonnées par les vraies avant mise en ligne.
// Le formulaire ci-dessous est volontairement statique : aucun service d'envoi
// (email/anti-spam) n'est encore branché derrière (§49) — ne pas le présenter
// comme fonctionnel tant qu'un vrai backend de contact n'existe pas.
const CONTACT_CHANNELS = [
  { label: "Email", value: "[email à renseigner]" },
  { label: "Téléphone", value: "[téléphone à renseigner]" },
  { label: "WhatsApp", value: "[à configurer]" },
];

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-foreground">Contactez-nous</h1>
      <p className="mt-2 text-muted">
        Une question sur une formation, un projet de formation d&apos;équipe ? Écrivez-nous.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {CONTACT_CHANNELS.map((channel) => (
          <div key={channel.label} className="rounded-xl border border-border bg-white p-4 text-center">
            <p className="text-xs font-semibold uppercase text-muted">{channel.label}</p>
            <p className="mt-1 text-sm text-foreground">{channel.value}</p>
          </div>
        ))}
      </div>

      <p className="mt-8 rounded-lg border border-dashed border-border bg-brand-light/40 p-4 text-sm text-muted">
        Le formulaire de contact et les coordonnées réelles seront ajoutés avant la mise en
        ligne publique — cette page est un espace réservé.
      </p>
    </div>
  );
}
