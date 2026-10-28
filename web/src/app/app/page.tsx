"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Eu } from "@/lib/api";
import ListaRelatorios, { type Resumo } from "@/components/ListaRelatorios";
import { MODOS } from "@/lib/modos";

export default function Painel() {
  const [eu, setEu] = useState<Eu | null>(null);
  const [relatorios, setRelatorios] = useState<Resumo[]>([]);

  useEffect(() => {
    api<Eu>("/api/eu").then(setEu).catch(() => {});
    api<Resumo[]>("/api/relatorios").then(setRelatorios).catch(() => {});
  }, []);

  return (
    <>
      <h1 style={{ fontSize: "clamp(1.6rem, 4vw, 2.2rem)", margin: "8px 0 4px" }}>O que você quer fazer hoje?</h1>
      {eu && (
        <p className="suave" style={{ marginBottom: 24 }}>
          {eu.analises_restantes} de {eu.cota_mensal} análises disponíveis neste mês (plano {eu.plano}).
        </p>
      )}
      <div className="grade" style={{ marginBottom: 40 }}>
        {MODOS.map((m) => (
          <Link key={m.modo} href={`/app/${m.modo}`} className="cartao">
            <span style={{ fontSize: "1.6rem" }} aria-hidden>{m.icone}</span>
            <h3 style={{ margin: "8px 0 4px" }}>{m.titulo}</h3>
            <p className="suave" style={{ fontSize: "0.93rem" }}>{m.descricao}</p>
          </Link>
        ))}
      </div>

      {relatorios.length > 0 && (
        <>
          <h2 style={{ fontSize: "1.4rem", marginBottom: 12 }}>Últimos relatórios</h2>
          <ListaRelatorios itens={relatorios.slice(0, 5)} />
          <Link href="/app/relatorios" className="btn btn-claro btn-pequeno" style={{ marginTop: 12 }}>
            Ver todos
          </Link>
        </>
      )}
    </>
  );
}
