"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function VerifyEntryPage() {
  const router = useRouter();
  const [code, setCode] = useState("");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (code.trim()) router.push(`/verify/${encodeURIComponent(code.trim())}`);
  }

  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-foreground">Vérifier un certificat</h1>
      <p className="mt-2 text-sm text-muted">
        Saisissez le code figurant sur le certificat (ex : SGT-2026-QGIS-000125).
      </p>
      <form onSubmit={handleSubmit} className="mt-6 flex gap-3">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="SGT-2026-XXXX-000000"
          className="flex-1 rounded-lg border border-border px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
        >
          Vérifier
        </button>
      </form>
    </div>
  );
}
