import Link from "next/link";
import type { CourseListItem } from "@/lib/api";

const LEVEL_LABELS: Record<CourseListItem["level"], string> = {
  BEGINNER: "Débutant",
  INTERMEDIATE: "Intermédiaire",
  ADVANCED: "Avancé",
};

function formatPrice(amount: string, currency: string) {
  const value = Number(amount);
  return `${value.toLocaleString("fr-FR")} ${currency}`;
}

export default function CourseCard({ course }: { course: CourseListItem }) {
  const hasPromo = course.promo_price !== null;

  return (
    <Link
      href={`/formations/${course.slug}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-border bg-white transition hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="flex h-40 items-center justify-center bg-brand-light text-brand">
        <span className="text-sm font-medium">
          {course.categories[0]?.name ?? "Formation"}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div className="flex items-center gap-2 text-xs font-medium text-muted">
          <span className="rounded-full bg-brand-light px-2 py-0.5 text-brand">
            {LEVEL_LABELS[course.level]}
          </span>
          {course.certificate_available && (
            <span className="rounded-full bg-brand-light px-2 py-0.5 text-brand">
              Certificat
            </span>
          )}
        </div>

        <h3 className="text-lg font-semibold text-foreground group-hover:text-brand">
          {course.title}
        </h3>
        <p className="line-clamp-2 flex-1 text-sm text-muted">{course.short_description}</p>

        <div className="flex items-center justify-between border-t border-border pt-3 text-sm text-muted">
          <span>{course.duration_hours} h · {course.modules_count} modules</span>
          <span>{course.students_count} apprenants</span>
        </div>

        <div className="flex items-baseline gap-2">
          {hasPromo && (
            <span className="text-sm text-muted line-through">
              {formatPrice(course.price, course.currency)}
            </span>
          )}
          <span className="text-lg font-bold text-brand">
            {formatPrice(hasPromo ? course.promo_price! : course.price, course.currency)}
          </span>
        </div>
      </div>
    </Link>
  );
}
