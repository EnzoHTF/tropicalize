"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITENS = [
  { href: "/app", icone: "🏠", rotulo: "Início" },
  { href: "/app/relatorios", icone: "📄", rotulo: "Relatórios" },
  { href: "/app/oportunidades", icone: "📅", rotulo: "Prazos" },
  { href: "/blog", icone: "📰", rotulo: "Notícias" },
  { href: "/app/conta", icone: "👤", rotulo: "Conta" },
];

/** Navegação inferior no celular, como num app nativo. */
export default function BarraApp() {
  const caminho = usePathname();
  return (
    <nav className="barra-app" aria-label="Navegação do app">
      {ITENS.map((i) => {
        const ativo = i.href === "/app" ? caminho === "/app" : caminho.startsWith(i.href);
        return (
          <Link key={i.href} href={i.href} aria-current={ativo ? "page" : undefined}>
            <span aria-hidden>{i.icone}</span>
            {i.rotulo}
          </Link>
        );
      })}
    </nav>
  );
}
