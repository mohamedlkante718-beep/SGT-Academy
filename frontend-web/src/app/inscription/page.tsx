"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError, login, register } from "@/lib/api";
import { storeTokens } from "@/lib/auth";

const COUNTRIES = [
  { code: "ML", label: "Mali" },
  { code: "SN", label: "Sénégal" },
  { code: "CI", label: "Côte d'Ivoire" },
  { code: "BF", label: "Burkina Faso" },
  { code: "GN", label: "Guinée" },
  { code: "NE", label: "Niger" },
  { code: "BJ", label: "Bénin" },
  { code: "TG", label: "Togo" },
  { code: "CM", label: "Cameroun" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    country: "ML",
    password: "",
    password_confirm: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (form.password !== form.password_confirm) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      await register(form);
      const tokens = await login(form.email, form.password);
      storeTokens(tokens.access, tokens.refresh);
      router.push("/formations");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const firstError = Object.values(err.body as Record<string, unknown>)[0];
        setError(Array.isArray(firstError) ? String(firstError[0]) : "Inscription impossible.");
      } else {
        setError("Inscription impossible. Vérifiez vos informations.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-foreground">Créer un compte</h1>
      <p className="mt-2 text-sm text-muted">
        Rejoignez SGT Academy pour accéder à nos formations.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <div className="flex gap-4">
          <label className="flex flex-1 flex-col gap-1 text-sm">
            Prénom
            <input
              required
              value={form.first_name}
              onChange={(e) => update("first_name", e.target.value)}
              className="rounded-lg border border-border px-3 py-2"
            />
          </label>
          <label className="flex flex-1 flex-col gap-1 text-sm">
            Nom
            <input
              required
              value={form.last_name}
              onChange={(e) => update("last_name", e.target.value)}
              className="rounded-lg border border-border px-3 py-2"
            />
          </label>
        </div>

        <label className="flex flex-col gap-1 text-sm">
          Email
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            className="rounded-lg border border-border px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Téléphone
          <input
            value={form.phone}
            onChange={(e) => update("phone", e.target.value)}
            placeholder="+223 70 00 00 00"
            className="rounded-lg border border-border px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Pays
          <select
            value={form.country}
            onChange={(e) => update("country", e.target.value)}
            className="rounded-lg border border-border px-3 py-2"
          >
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Mot de passe
          <input
            type="password"
            required
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            className="rounded-lg border border-border px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Confirmer le mot de passe
          <input
            type="password"
            required
            value={form.password_confirm}
            onChange={(e) => update("password_confirm", e.target.value)}
            className="rounded-lg border border-border px-3 py-2"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-2 rounded-lg bg-brand px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
        >
          {loading ? "Création..." : "Créer mon compte"}
        </button>
      </form>

      <p className="mt-6 text-sm text-muted">
        Déjà un compte ?{" "}
        <Link href="/connexion" className="font-semibold text-brand hover:underline">
          Se connecter
        </Link>
      </p>
    </div>
  );
}
