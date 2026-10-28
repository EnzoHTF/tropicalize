"use client";

import { useEffect, useState } from "react";
import ListaRelatorios, { type Resumo } from "@/components/ListaRelatorios";
import { api } from "@/lib/api";

export default function Relatorios() {
  const [itens, setItens] = useState<Resumo[] | null>(null);
  useEffect(() => {
    api<Resumo[]>("/api/relatorios").then(setItens).catch(() => setItens([]));
  }, []);

  return (
    <div className="wrap-estreito" style={{ padding: 0 }}>
      <h1 style={{ fontSize: "1.9rem", margin: "8px 0 20px" }}>Seus relatórios</h1>
      {itens === null ? (
        <p className="status-vivo">Carregando</p>
      ) : itens.length ? (
        <ListaRelatorios itens={itens} />
      ) : (
        <p className="suave">Você ainda não gerou nenhuma análise.</p>
      )}
    </div>
  );
}
