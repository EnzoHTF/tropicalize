"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Item = {
  id: number;
  nome: string;
  tipo: string;
  inscricao_fecha: string | null;
  ticket_texto: string | null;
  link: string | null;
  aderencia?: number;
  salvo?: boolean;
};

const data = (d: string) => new Date(d + "T12:00").toLocaleDateString("pt-BR");

function Linha({ i, aoSalvar }: { i: Item; aoSalvar?: () => void }) {
  return (
    <div className="cartao" style={{ padding: "14px 18px", display: "flex", gap: 12, justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
      <div>
        <b>{i.nome}</b>
        <div className="suave" style={{ fontSize: "0.85rem" }}>
          {i.inscricao_fecha ? `Inscrições até ${data(i.inscricao_fecha)}` : "Fluxo contínuo ou prazo não informado"}
          {i.ticket_texto && ` · ${i.ticket_texto}`}
          {i.aderencia !== undefined && ` · aderência ${i.aderencia}%`}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        {aoSalvar && (
          <button className="btn btn-claro btn-pequeno" onClick={aoSalvar} aria-pressed={i.salvo}>
            {i.salvo ? "★ Salvo" : "☆ Salvar"}
          </button>
        )}
        {i.link && (
          <a className="btn btn-pequeno" href={i.link} target="_blank" rel="noopener noreferrer">Inscrever-se</a>
        )}
      </div>
    </div>
  );
}

export default function Oportunidades() {
  const [dados, setDados] = useState<{ recomendadas: Item[]; abertas: Item[] } | null>(null);
  useEffect(() => {
    api<{ recomendadas: Item[]; abertas: Item[] }>("/api/oportunidades").then(setDados).catch(() => {});
  }, []);

  async function alternar(id: number) {
    const { salvo } = await api<{ salvo: boolean }>(`/api/recomendacoes/${id}/salvar`, { method: "POST" });
    setDados((d) => d && { ...d, recomendadas: d.recomendadas.map((i) => (i.id === id ? { ...i, salvo } : i)) });
  }

  if (!dados) return <p className="status-vivo">Carregando</p>;
  return (
    <div className="wrap-estreito" style={{ padding: 0 }}>
      <h1 style={{ fontSize: "1.9rem", margin: "8px 0 6px" }}>Prazos de inscrição</h1>
      <p className="suave" style={{ marginBottom: 20 }}>
        Salve as opções que interessam: avisamos no celular 7 dias e 1 dia antes de fechar.{" "}
        <Link href="/app/conta" style={{ color: "var(--folha)" }}>Ativar notificações</Link>
      </p>
      <h2 style={{ fontSize: "1.3rem", marginBottom: 10 }}>Recomendadas para você</h2>
      {dados.recomendadas.length ? (
        <div style={{ display: "grid", gap: 10, marginBottom: 32 }}>
          {dados.recomendadas.map((i) => <Linha key={i.id} i={i} aoSalvar={() => alternar(i.id)} />)}
        </div>
      ) : (
        <p className="suave" style={{ marginBottom: 32 }}>
          Faça uma análise no modo <Link href="/app/captar" style={{ color: "var(--folha)" }}>Captar investimento</Link> para receber recomendações.
        </p>
      )}
      <h2 style={{ fontSize: "1.3rem", marginBottom: 10 }}>Fechando nos próximos 45 dias</h2>
      <div style={{ display: "grid", gap: 10 }}>
        {dados.abertas.map((i) => <Linha key={i.id} i={i} />)}
        {!dados.abertas.length && <p className="suave">Nenhum prazo próximo na base agora.</p>}
      </div>
    </div>
  );
}
