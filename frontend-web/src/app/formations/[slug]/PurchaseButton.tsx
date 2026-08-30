"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, purchaseCourse, submitManualProof } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; reference: string; amount: string; currency: string }
  | { status: "error"; message: string };

type ProofState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "sent" }
  | { status: "error"; message: string };

export default function PurchaseButton({ slug }: { slug: string }) {
  const [state, setState] = useState<State>({ status: "idle" });
  const [proofState, setProofState] = useState<ProofState>({ status: "idle" });
  const [transactionRef, setTransactionRef] = useState("");
  const [proofFile, setProofFile] = useState<File | null>(null);
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

  async function handleSubmitProof(event: React.FormEvent, paymentReference: string) {
    event.preventDefault();
    setProofState({ status: "loading" });
    try {
      await submitManualProof(paymentReference, token!, transactionRef, proofFile ?? undefined);
      setProofState({ status: "sent" });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? (error.body as { reference?: string[]; detail?: string })?.reference?.[0] ??
            (error.body as { detail?: string })?.detail ??
            "Impossible d'envoyer votre preuve de paiement."
          : "Impossible d'envoyer votre preuve de paiement.";
      setProofState({ status: "error", message });
    }
  }

  if (state.status === "success") {
    const amount = Number(state.amount).toLocaleString("fr-FR");
    const whatsappMessage = encodeURIComponent(
      `Bonjour, je viens de payer ${amount} ${state.currency} pour une formation SGT Academy. Référence : ${state.reference}. Voici ma preuve de paiement.`
    );
    return (
      <div className="mt-6 rounded-lg border border-brand bg-brand-light p-4 text-sm text-foreground">
        <p className="font-semibold">Paiement enregistré (en attente de validation)</p>
        <p className="mt-1">
          Référence : <span className="font-mono">{state.reference}</span>
          <br />
          Montant : {amount} {state.currency}
        </p>

        <div className="mt-3 rounded-lg border border-border bg-white p-3">
          <p className="font-semibold">Comment payer</p>
          <ol className="mt-1 list-decimal space-y-1 pl-4 text-muted">
            <li>
              Envoyez <strong>{amount} {state.currency}</strong> via <strong>Orange Money</strong> au{" "}
              <strong>+223 73 23 16 47</strong> ou au <strong>+223 79 16 16 44</strong>, ou via{" "}
              <strong>Moov Money</strong> au <strong>+223 66 56 26 86</strong>.
            </li>
            <li>
              Indiquez la référence <span className="font-mono">{state.reference}</span> dans le
              motif du transfert si possible.
            </li>
            <li>Confirmez votre paiement ci-dessous avec la référence de la transaction.</li>
          </ol>

          {proofState.status === "sent" ? (
            <p className="mt-3 rounded-lg bg-brand-light p-3 font-semibold text-brand-dark">
              Preuve envoyée. Votre accès sera débloqué après validation.
            </p>
          ) : (
            <form
              onSubmit={(e) => handleSubmitProof(e, state.reference)}
              className="mt-3 flex flex-col gap-2"
            >
              <label className="flex flex-col gap-1 text-sm">
                Référence de la transaction Mobile Money
                <input
                  required
                  value={transactionRef}
                  onChange={(e) => setTransactionRef(e.target.value)}
                  placeholder="Ex : MP240830.1234.A56789"
                  className="rounded-lg border border-border px-3 py-2"
                />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                Capture d&apos;écran (optionnel, PNG/JPEG/PDF, 5 Mo max)
                <input
                  type="file"
                  accept="image/png,image/jpeg,application/pdf"
                  onChange={(e) => setProofFile(e.target.files?.[0] ?? null)}
                  className="text-sm"
                />
              </label>
              <button
                type="submit"
                disabled={proofState.status === "loading"}
                className="mt-1 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
              >
                {proofState.status === "loading" ? "Envoi..." : "Confirmer mon paiement"}
              </button>
              {proofState.status === "error" && (
                <p className="text-sm text-red-600">{proofState.message}</p>
              )}
            </form>
          )}

          <a
            href={`https://wa.me/22373231647?text=${whatsappMessage}`}
            className="mt-3 block text-center text-sm font-semibold text-brand hover:underline"
          >
            Ou envoyez votre preuve par WhatsApp
          </a>
        </div>

        <p className="mt-2 text-muted">
          Votre accès sera débloqué après validation de votre paiement par un administrateur
          (généralement sous 24h).
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
