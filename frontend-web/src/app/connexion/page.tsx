"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError, login, resendVerificationCode, verifyEmail } from "@/lib/api";
import { storeTokens } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNeedsVerification(false);
    setLoading(true);
    try {
      const tokens = await login(email, password);
      storeTokens(tokens.access, tokens.refresh);
      router.push("/formations");
      router.refresh();
    } catch (err) {
      const body = err instanceof ApiError ? (err.body as { non_field_errors?: string[] }) : null;
      if (err instanceof ApiError && err.status === 400 && body?.non_field_errors) {
        setError(body.non_field_errors[0]);
        setNeedsVerification(true);
      } else {
        setError("Email ou mot de passe incorrect.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await verifyEmail(email, code);
      const tokens = await login(email, password);
      storeTokens(tokens.access, tokens.refresh);
      router.push("/formations");
      router.refresh();
    } catch {
      setError("Code incorrect ou expiré.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setError(null);
    setInfo(null);
    try {
      await resendVerificationCode(email);
      setInfo("Un nouveau code vient d'être envoyé à votre adresse email.");
    } catch {
      setError("Impossible d'envoyer un nouveau code.");
    }
  }

  if (needsVerification) {
    return (
      <div className="mx-auto flex max-w-md flex-col px-4 py-16 sm:px-6">
        <h1 className="text-2xl font-bold text-foreground">Vérifiez votre email</h1>
        <p className="mt-2 text-sm text-muted">
          Entrez le code à 6 chiffres envoyé à <strong>{email}</strong>.
        </p>

        <form onSubmit={handleVerify} className="mt-8 flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Code de vérification
            <input
              required
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              placeholder="123456"
              className="rounded-lg border border-border px-3 py-2 text-center text-lg tracking-widest"
            />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {info && <p className="text-sm text-brand">{info}</p>}

          <button
            type="submit"
            disabled={loading || code.length !== 6}
            className="mt-2 rounded-lg bg-brand px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
          >
            {loading ? "Vérification..." : "Valider mon compte"}
          </button>

          <button
            type="button"
            onClick={handleResend}
            className="text-sm font-semibold text-brand hover:underline"
          >
            Je n&apos;ai pas reçu de code — renvoyer
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-foreground">Connexion</h1>
      <p className="mt-2 text-sm text-muted">
        Accédez à vos formations SGT Academy.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-lg border border-border px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Mot de passe
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-lg border border-border px-3 py-2"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-2 rounded-lg bg-brand px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>

      <p className="mt-6 text-sm text-muted">
        Pas encore de compte ?{" "}
        <Link href="/inscription" className="font-semibold text-brand hover:underline">
          Créer un compte
        </Link>
      </p>
    </div>
  );
}
