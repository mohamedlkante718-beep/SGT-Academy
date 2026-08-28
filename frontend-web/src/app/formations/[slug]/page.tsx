import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ApiError, getCourseBySlug } from "@/lib/api";
import PurchaseButton from "./PurchaseButton";

type Props = { params: Promise<{ slug: string }> };

async function loadCourse(slug: string) {
  try {
    return await getCourseBySlug(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const course = await loadCourse(slug);
  if (!course) return {};
  return {
    title: course.seo_title || course.title,
    description: course.seo_description || course.short_description,
  };
}

const LEVEL_LABELS: Record<string, string> = {
  BEGINNER: "Débutant",
  INTERMEDIATE: "Intermédiaire",
  ADVANCED: "Avancé",
};

function formatPrice(amount: string, currency: string) {
  return `${Number(amount).toLocaleString("fr-FR")} ${currency}`;
}

export default async function CourseDetailPage({ params }: Props) {
  const { slug } = await params;
  const course = await loadCourse(slug);
  if (!course) notFound();

  const hasPromo = course.promo_price !== null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="grid gap-10 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium">
            {course.categories.map((category) => (
              <span key={category.id} className="rounded-full bg-brand-light px-2 py-1 text-brand">
                {category.name}
              </span>
            ))}
            <span className="rounded-full bg-brand-light px-2 py-1 text-brand">
              {LEVEL_LABELS[course.level] ?? course.level}
            </span>
          </div>

          <h1 className="mt-4 text-3xl font-bold text-foreground">{course.title}</h1>
          <p className="mt-3 text-lg text-muted">{course.short_description}</p>

          <div className="mt-6 flex flex-wrap gap-6 text-sm text-muted">
            <span>⏱ {course.duration_hours} heures</span>
            <span>📚 {course.modules.length} modules</span>
            <span>👥 {course.students_count} apprenants</span>
            {course.certificate_available && <span>🎓 Certificat inclus</span>}
          </div>

          {course.description && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold text-foreground">Description</h2>
              <p className="mt-3 whitespace-pre-line text-muted">{course.description}</p>
            </section>
          )}

          {course.objectives.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold text-foreground">Objectifs</h2>
              <ul className="mt-3 list-inside list-disc space-y-1 text-muted">
                {course.objectives.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}

          {course.skills_acquired.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold text-foreground">Compétences acquises</h2>
              <ul className="mt-3 list-inside list-disc space-y-1 text-muted">
                {course.skills_acquired.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}

          {course.prerequisites.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold text-foreground">Prérequis</h2>
              <ul className="mt-3 list-inside list-disc space-y-1 text-muted">
                {course.prerequisites.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}

          <section className="mt-10">
            <h2 className="text-xl font-semibold text-foreground">Programme</h2>
            <div className="mt-4 space-y-3">
              {course.modules.map((module, index) => (
                <div key={module.id} className="rounded-xl border border-border bg-white p-5">
                  <h3 className="font-semibold text-foreground">
                    Module {index + 1} — {module.title}
                  </h3>
                  <ul className="mt-3 space-y-2 text-sm text-muted">
                    {module.lessons.map((lesson) => (
                      <li key={lesson.id} className="flex items-center justify-between">
                        <span>
                          {lesson.title}
                          {lesson.is_preview && (
                            <span className="ml-2 text-xs font-semibold text-brand">Aperçu gratuit</span>
                          )}
                        </span>
                        <span>{Math.round(lesson.duration_seconds / 60)} min</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          {course.instructors.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold text-foreground">Formateur</h2>
              <div className="mt-3 space-y-2">
                {course.instructors.map((instructor) => (
                  <div key={instructor.id}>
                    <p className="font-medium text-foreground">{instructor.full_name}</p>
                    <p className="text-sm text-muted">{instructor.headline}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        <aside className="h-fit rounded-xl border border-border bg-white p-6 lg:sticky lg:top-24">
          <div className="flex items-baseline gap-2">
            {hasPromo && (
              <span className="text-sm text-muted line-through">
                {formatPrice(course.price, course.currency)}
              </span>
            )}
            <span className="text-2xl font-bold text-brand">
              {formatPrice(hasPromo ? course.promo_price! : course.price, course.currency)}
            </span>
          </div>

          <PurchaseButton slug={course.slug} />

          <p className="mt-4 text-xs text-muted">
            Paiement manuel disponible dès aujourd&apos;hui (Mobile Money/carte à venir).
            L&apos;accès est débloqué après validation par un administrateur.
          </p>
        </aside>
      </div>
    </div>
  );
}
