"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import BarraApp from "@/components/BarraApp";
import Topo from "@/components/Topo";
import { useSessao } from "@/lib/supabase";

/** Área logada: exige sessão e mostra a navegação do app. */
export default function LayoutApp({ children }: { children: React.ReactNode }) {
  const sessao = useSessao();
  const router = useRouter();
  const caminho = usePathname();

  useEffect(() => {
    if (sessao === null) router.replace(`/entrar?volta=${encodeURIComponent(caminho)}`);
  }, [sessao, caminho, router]);

  return (
    <div className="com-barra">
      <div className="wrap">
        <Topo
          direita={
            <>
              <Link href="/app/relatorios" className="so-desktop">Relatórios</Link>
              <Link href="/app/oportunidades" className="so-desktop">Prazos</Link>
              <Link href="/app/conta" className="so-desktop">Conta</Link>
            </>
          }
        />
      </div>
      <main className="wrap" style={{ paddingBottom: 48 }}>
        {sessao ? children : <p className="status-vivo">Carregando…</p>}
      </main>
      <BarraApp />
    </div>
  );
}
