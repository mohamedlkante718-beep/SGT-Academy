import Link from "next/link";
import CourseCard from "@/components/CourseCard";
import { getCourses } from "@/lib/api";

const ADVANTAGES = [
  {
    title: "Formateurs experts",
    description: "Des professionnels expérimentés dans leur domaine.",
  },
  {
    title: "Certificat vérifiable",
    description: "Chaque certificat est authentifiable en ligne, gratuitement.",
  },
  {
    title: "Accessible partout",
    description: "Optimisé pour les connexions limitées, sur ordinateur ou téléphone.",
  },
];

export default async function HomePage() {
  const popularCourses = await getCourses({ ordering: "-created_at" }).catch(() => null);

  return (
    <div>
      <section className="bg-brand-light">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 py-20 text-center sm:px-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-brand">
            Safe Green Tech · SGT Academy
          </p>
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            Développez vos compétences.
            <br />
            Construisez votre avenir.
          </h1>
          <p className="max-w-xl text-lg text-muted">
            Des formations professionnelles variées, conçues pour développer vos
            compétences et faire progresser votre carrière.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/formations"
              className="rounded-lg bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark"
            >
              Explorer les formations
            </Link>
            <Link
              href="/inscription"
              className="rounded-lg border border-brand px-6 py-3 text-sm font-semibold text-brand transition hover:bg-white"
            >
              Commencer maintenant
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="flex items-end justify-between">
          <h2 className="text-2xl font-bold text-foreground">Formations populaires</h2>
          <Link href="/formations" className="text-sm font-semibold text-brand hover:underline">
            Voir tout le catalogue →
          </Link>
        </div>

        {!popularCourses && (
          <p className="mt-8 rounded-lg border border-border bg-white p-6 text-sm text-muted">
            Le catalogue n&apos;a pas pu être chargé pour le moment. Le serveur API est-il démarré ?
          </p>
        )}

        {popularCourses && popularCourses.results.length === 0 && (
          <p className="mt-8 rounded-lg border border-border bg-white p-6 text-sm text-muted">
            Aucune formation publiée pour le moment.
          </p>
        )}

        {popularCourses && popularCourses.results.length > 0 && (
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {popularCourses.results.slice(0, 6).map((course) => (
              <CourseCard key={course.slug} course={course} />
            ))}
          </div>
        )}
      </section>

      <section className="border-t border-border bg-white">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <h2 className="text-2xl font-bold text-foreground">Pourquoi SGT Academy ?</h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            {ADVANTAGES.map((item) => (
              <div key={item.title} className="rounded-xl border border-border p-6">
                <h3 className="font-semibold text-foreground">{item.title}</h3>
                <p className="mt-2 text-sm text-muted">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-brand">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-4 py-16 text-center sm:px-6">
          <h2 className="text-2xl font-bold text-white">
            Besoin de former toute votre équipe ?
          </h2>
          <p className="max-w-xl text-brand-light">
            Contactez-nous pour une offre entreprise adaptée à vos besoins.
          </p>
          <Link
            href="/contact"
            className="rounded-lg bg-white px-6 py-3 text-sm font-semibold text-brand transition hover:bg-brand-light"
          >
            Nous contacter
          </Link>
        </div>
      </section>
    </div>
  );
}
