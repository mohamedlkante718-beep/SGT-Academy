import type { Metadata } from "next";
import Link from "next/link";
import { verifyCertificate } from "@/lib/api";

type Props = { params: Promise<{ code: string }> };

export const metadata: Metadata = {
  title: "Vérification de certificat",
  description: "Vérifiez l'authenticité d'un certificat SGT Academy.",
};

export default async function VerifyCertificatePage({ params }: Props) {
  const { code } = await params;
  const result = await verifyCertificate(code).catch(() => null);

  if (!result) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center sm:px-6">
        <p className="text-muted">Service de vérification indisponible pour le moment.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16 sm:px-6">
      <div
        className={`rounded-xl border p-8 text-center ${
          result.valid ? "border-brand bg-brand-light" : "border-red-200 bg-red-50"
        }`}
      >
        <p className={`text-lg font-bold ${result.valid ? "text-brand" : "text-red-700"}`}>
          {result.valid ? "CERTIFICAT VALIDE" : "CERTIFICAT INVALIDE"}
        </p>

        {result.valid ? (
          <dl className="mt-6 space-y-3 text-left text-sm">
            <div>
              <dt className="text-muted">Nom</dt>
              <dd className="font-semibold text-foreground">{result.learner_name}</dd>
            </div>
            <div>
              <dt className="text-muted">Formation</dt>
              <dd className="font-semibold text-foreground">{result.course_title}</dd>
            </div>
            <div>
              <dt className="text-muted">Date</dt>
              <dd className="font-semibold text-foreground">
                {result.issued_at && new Date(result.issued_at).toLocaleDateString("fr-FR")}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Numéro</dt>
              <dd className="font-mono font-semibold text-foreground">{result.code}</dd>
            </div>
          </dl>
        ) : (
          <p className="mt-4 text-sm text-red-700">
            Aucun certificat valide ne correspond au code « {result.code} ».
          </p>
        )}
      </div>

      <p className="mt-6 text-center text-sm text-muted">
        <Link href="/verify" className="font-semibold text-brand hover:underline">
          Vérifier un autre certificat
        </Link>
      </p>
    </div>
  );
}
