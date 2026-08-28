"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, purchaseCourse } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; reference: string; amount: string; currency: string }
  | { status: "error"; message: string };

export default function PurchaseButton({ slug }: { slug: string }) {
  const [state, setState] = useState<State>({ status: "idle" });
  // Le token vient du localStorage, indisponible côté serveur : on ne le lit
  // qu'après le montage pour éviter un décalage d'hydratation SSR/client.
  const [token, setToken] = useState<string | null>(null);

  // Lecture localStorage volontairement différée au montage (via useEffect) pour
  // éviter un décalage d'hydratation SSR/client (le token n'existe pas côté serveur).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setToken(getAccessToken());
  }, []);

  if (!token) {
    return (
      <Link
        href="/inscription"
        className="mt-6 block w-full rounded-lg bg-brand px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-brand-dark"
      >
        Créer un compte pour acheter
      </Link>
    );
  }

  async function handlePurchase() {
    setState({ status: "loading" });
    try {
      const payment = await purchaseCourse(slug, token!);
      setState({
        status: "success",
        reference: payment.reference,
        amount: payment.amount,
        currency: payment.currency,
      });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? (error.body as { error?: string; detail?: string })?.error ??
            (error.body as { detail?: string })?.detail ??
            "Impossible de démarrer l'achat."
          : "Impossible de démarrer l'achat.";
      setState({ status: "error", message });
    }
  }

  if (state.status === "success") {
    return (
      <div className="mt-6 rounded-lg border border-brand bg-brand-light p-4 text-sm text-foreground">
        <p className="font-semibold">Paiement enregistré (en attente de validation)</p>
        <p className="mt-1">
          Référence : <span className="font-mono">{state.reference}</span>
          <br />
          Montant : {Number(state.amount).toLocaleString("fr-FR")} {state.currency}
        </p>
        <p className="mt-2 text-muted">
          Suivez les instructions de paiement manuel qui vous seront communiquées, puis
          votre accès sera débloqué après validation par un administrateur.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-6">
      <button
        type="button"
        onClick={handlePurchase}
        disabled={state.status === "loading"}
        className="block w-full rounded-lg bg-brand px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
      >
        {state.status === "loading" ? "Démarrage..." : "Acheter la formation"}
      </button>
      {state.status === "error" && (
        <p className="mt-2 text-sm text-red-600">{state.message}</p>
      )}
    </div>
  );
}
