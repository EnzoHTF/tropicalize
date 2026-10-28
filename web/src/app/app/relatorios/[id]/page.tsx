"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Fontes from "@/components/Fontes";
import Markdown from "@/components/Markdown";
import Recomendacoes from "@/components/Recomendacoes";
import { api, ErroApi, type Relatorio } from "@/lib/api";
import { compartilhar } from "@/lib/compartilhar";

export default function VerRelatorio() {
  const { id } = useParams<{ id: string }>();
  const [rel, setRel] = useState<Relatorio | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    let ativo = true;
    let timer: ReturnType<typeof setTimeout>;
    const carregar = () =>
      api<Relatorio>(`/api/relatorios/${id}`)
        .then((r) => {
          if (!ativo) return;
          setRel(r);
          if (r.status === "gerando") timer = setTimeout(carregar, 5000); // ainda gerando em segundo plano
        })
        .catch((e) => setErro(e instanceof ErroApi ? e.message : "Não foi possível abrir o relatório."));
    carregar();
    return () => {
      ativo = false;
      clearTimeout(timer);
    };
  }, [id]);

  if (erro) return <p className="erro">{erro}</p>;
  if (!rel) return <p className="status-vivo">Carregando</p>;

  return (
    <div className="wrap-estreito" style={{ padding: 0 }}>
      <Link href="/app/relatorios" className="suave" style={{ fontSize: "0.9rem" }}>← Relatórios</Link>
      <h1 style={{ fontSize: "clamp(1.4rem, 4vw, 1.9rem)", margin: "10px 0 4px" }}>{rel.titulo}</h1>
      <p className="suave" style={{ fontSize: "0.88rem", marginBottom: 16 }}>
        {new Date(rel.criado_em).toLocaleString("pt-BR")}
        {rel.status === "gerando" && " · ainda gerando, a página atualiza sozinha"}
        {rel.status === "erro" && " · a análise não terminou"}
      </p>
      {rel.status === "gerando" && !rel.conteudo && <p className="status-vivo">Gerando o relatório</p>}
      {rel.conteudo && (
        <article className="cartao">
          <Markdown texto={rel.conteudo} />
        </article>
      )}
      <Recomendacoes itens={rel.estruturado ?? []} />
      <Fontes fontes={rel.fontes} />
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 24 }}>
        {rel.modo !== "captar" && rel.status === "pronto" && (
          <Link href={`/app/captar?origem=${rel.id}`} className="btn">Buscar investidores para isso →</Link>
        )}
        <button className="btn btn-claro" onClick={() => compartilhar(rel.titulo, rel.conteudo)}>
          Compartilhar
        </button>
      </div>
    </div>
  );
}
