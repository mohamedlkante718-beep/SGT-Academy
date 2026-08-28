import Link from "next/link";

const NAV_LINKS = [
  { href: "/formations", label: "Formations" },
  { href: "/tarifs", label: "Tarifs" },
  { href: "/contact", label: "Contact" },
];

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <svg width="36" height="36" viewBox="0 0 100 100" aria-hidden>
            <rect x="8" y="8" width="84" height="84" rx="22" fill="#1e7a46" />
            <text x="50" y="63" fontFamily="Sora, sans-serif" fontWeight="800" fontSize="34" fill="#ffffff" textAnchor="middle">
              SGT
            </text>
          </svg>
          <span className="font-[family-name:var(--font-display)] text-lg font-bold tracking-tight text-foreground">
            SGT Academy
          </span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted transition hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/connexion"
            className="text-sm font-medium text-muted transition hover:text-foreground"
          >
            Connexion
          </Link>
          <Link
            href="/inscription"
            className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
          >
            Inscription
          </Link>
        </div>
      </div>
    </header>
  );
}
