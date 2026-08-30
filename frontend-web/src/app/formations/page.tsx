import type { Metadata } from "next";
import CourseCard from "@/components/CourseCard";
import { getCourses } from "@/lib/api";

export const metadata: Metadata = {
  title: "Formations",
  description:
    "Découvrez le catalogue des formations SGT Academy : des formations professionnelles variées pour développer vos compétences.",
};

const LEVELS = [
  { value: "", label: "Tous niveaux" },
  { value: "BEGINNER", label: "Débutant" },
  { value: "INTERMEDIATE", label: "Intermédiaire" },
  { value: "ADVANCED", label: "Avancé" },
];

type SearchParams = {
  search?: string;
  level?: string;
  certificate_available?: string;
  min_price?: string;
  max_price?: string;
};

export default async function CataloguePage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  const courses = await getCourses({
    search: params.search,
    level: params.level,
    certificate_available: params.certificate_available === "on" ? true : undefined,
    min_price: params.min_price ? Number(params.min_price) : undefined,
    max_price: params.max_price ? Number(params.max_price) : undefined,
  }).catch(() => null);

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold text-foreground">Nos formations</h1>
      <p className="mt-2 text-muted">
        Des formations professionnelles variées, pour développer vos compétences à
        votre rythme.
      </p>

      <form className="mt-8 grid gap-4 rounded-xl border border-border bg-white p-6 sm:grid-cols-2 lg:grid-cols-5">
        <input
          type="text"
          name="search"
          defaultValue={params.search}
          placeholder="Rechercher une formation..."
          className="rounded-lg border border-border px-3 py-2 text-sm lg:col-span-2"
        />
        <select
          name="level"
          defaultValue={params.level ?? ""}
          className="rounded-lg border border-border px-3 py-2 text-sm"
        >
          {LEVELS.map((level) => (
            <option key={level.value} value={level.value}>
              {level.label}
            </option>
          ))}
        </select>
        <input
          type="number"
          name="max_price"
          defaultValue={params.max_price}
          placeholder="Prix max (FCFA)"
          className="rounded-lg border border-border px-3 py-2 text-sm"
        />
        <label className="flex items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            name="certificate_available"
            defaultChecked={params.certificate_available === "on"}
          />
          Avec certificat
        </label>
        <button
          type="submit"
          className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark lg:col-span-5"
        >
          Filtrer
        </button>
      </form>

      {!courses && (
        <p className="mt-10 rounded-lg border border-border bg-white p-6 text-sm text-muted">
          Le catalogue n&apos;a pas pu être chargé. Le serveur API est-il démarré ?
        </p>
      )}

      {courses && courses.results.length === 0 && (
        <p className="mt-10 rounded-lg border border-border bg-white p-6 text-sm text-muted">
          Aucune formation ne correspond à ces critères.
        </p>
      )}

      {courses && courses.results.length > 0 && (
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {courses.results.map((course) => (
            <CourseCard key={course.slug} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
