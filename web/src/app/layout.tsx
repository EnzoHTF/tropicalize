import type { Metadata, Viewport } from "next";
import { Fraunces, Inter } from "next/font/google";
import { SITE_URL } from "@/lib/config";
import RegistrarSW from "@/components/RegistrarSW";
import "./globals.css";

const fraunces = Fraunces({ subsets: ["latin"], weight: ["600", "700"], variable: "--font-fraunces" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Tropicalize · IA para empreender no Brasil", template: "%s · Tropicalize" },
  description:
    "Descubra ideias que deram certo lá fora, diagnostique sua empresa, valide e viabilize sua ideia e encontre fundos e aceleradoras para captar investimento.",
  applicationName: "Tropicalize",
  appleWebApp: { capable: true, title: "Tropicalize", statusBarStyle: "default" },
  icons: { icon: "/logo.svg", apple: "/icones/apple-touch-icon.png" },
  openGraph: { siteName: "Tropicalize", locale: "pt_BR", type: "website" },
  alternates: { types: { "application/rss+xml": `${SITE_URL}/blog/feed.xml` } },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FBF7EF" },
    { media: "(prefers-color-scheme: dark)", color: "#0F1714" },
  ],
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${fraunces.variable} ${inter.variable}`}>
      <body>
        {children}
        <RegistrarSW />
      </body>
    </html>
  );
}
