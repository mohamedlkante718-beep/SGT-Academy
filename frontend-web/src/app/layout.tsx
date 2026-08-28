import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "SGT Academy — Développez vos compétences. Construisez votre avenir.",
    template: "%s — SGT Academy",
  },
  description:
    "SGT Academy, la plateforme de formation en ligne de Safe Green Tech : SIG, environnement, technologie et compétences professionnelles pour le Mali et l'Afrique francophone.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
