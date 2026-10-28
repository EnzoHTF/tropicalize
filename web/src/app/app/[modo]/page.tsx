"use client";

import Link from "next/link";
import { notFound, useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import Fontes from "@/components/Fontes";
import Markdown from "@/components/Markdown";
import Recomendacoes from "@/components/Recomendacoes";
import { analisar, api, ErroApi, type Recomendacao, type Relatorio } from "@/lib/api";
import { type Campo, modoPorNome } from "@/lib/modos";

type Valores = Record<string, string | boolean>;

function valorInicial(c: Campo): string | boolean {
  if (c.tipo === "booleano") return c.padrao === undefined ? false : Boolean(c.padrao);
  if (Array.isArray(c.padrao)) return c.padrao.join(", ");
  return c.padrao === undefined ? "" : String(c.padrao);
}

function montarEntrada(campos: Campo[], valores: Valores): Record<string, unknown> {
  const entrada: Record<string, unknown> = {};
  for (const c of campos) {
    const v = valores[c.nome];
    if (c.tipo === "booleano") entrada[c.nome] = Boolean(v);
    else if (c.tipo === "numero") {
      if (v !== "") entrada[c.nome] = Number(String(v).replace(/\./g, "").replace(",", "."));
    } else if (c.tipo === "lista") entrada[c.nome] = String(v).split(",").map((x) => x.trim()).filter(Boolean);
    else if (String(v).trim()) entrada[c.nome] = String(v).trim();
  }
  return entrada;
}

function Tela() {
  const { modo } = useParams<{ modo: string }>();
  const origemId = useSearchParams().get("origem");
  const def = modoPorNome(modo);
  if (!def) notFound();

  const [valores, setValores] = useState<Valores>(() =>
    Object.fromEntries(def.campos.map((c) => [c.nome, valorInicial(c)])),
  );
  const [origem, setOrigem] = useState<Relatorio | null>(null);
  const [gerando, setGerando] = useState(false);
  const [status, setStatus] = useState("");
  const [texto, setTexto] = useState("");
  const [fontes, setFontes] = useState<{ titulo: string; url: string }[]>([]);
  const [recs, setRecs] = useState<Recomendacao[]>([]);
  const [relatorioId, setRelatorioId] = useState<number | null>(null);
  const [erro, setErro] = useState("");
  const abortar = useRef<AbortController | null>(null);

  // "Levar para Captar": reaproveita a descrição de um relatório anterior
  useEffect(() => {
    if (!origemId) return;
    api<Relatorio>(`/api/relatorios/${origemId}`)
      .then((r) => {
        setOrigem(r);
        const e = r.entrada as Record<string, string>;
        const descricao = e.descricao || e.ideia || e.tema || "";
        if (descricao) setValores((v) => ({ ...v, descricao: v.descricao || descricao, setor: v.setor || e.setor || "" }));
      })
      .catch(() => {});
  }, [origemId]);

  useEffect(() => () => abortar.current?.abort(), []);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setTexto("");
    setFontes([]);
    setRecs([]);
    setRelatorioId(null);
    setGerando(true);
    setStatus("Iniciando a análise");
    abortar.current = new AbortController();
    const entrada = montarEntrada(def!.campos, valores);
    if (origem && def!.modo === "captar") entrada.relatorio_origem_id = origem.id;
    try {
      await analisar(def!.modo, entrada, (ev) => {
        switch (ev.tipo) {
          case "inicio": setRelatorioId(ev.relatorio_id); break;
          case "status": setStatus(ev.texto); break;
          case "texto": setStatus(""); setTexto((t) => t + ev.texto); break;
          case "fonte": setFontes((f) => [...f, { titulo: ev.titulo, url: ev.url }]); break;
          case "recomendacoes": setRecs(ev.itens); break;
          case "erro": setErro(ev.texto); break;
        }
      }, abortar.current.signal);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setErro(err instanceof ErroApi ? err.message : "Conexão interrompida. O relatório continua sendo gerado e aparece em Relatórios.");
      }
    } finally {
      setGerando(false);
      setStatus("");
    }
  }

  const terminou = !gerando && texto && !erro;

  return (
    <div className="wrap-estreito" style={{ padding: 0 }}>
      <Link href="/app" className="suave" style={{ fontSize: "0.9rem" }}>← Voltar</Link>
      <h1 style={{ fontSize: "clamp(1.6rem, 4vw, 2.1rem)", margin: "10px 0 4px" }}>
        <span aria-hidden>{def.icone}</span> {def.titulo}
      </h1>
      <p className="suave" style={{ marginBottom: 20 }}>{def.descricao}</p>

      {!texto && !gerando && (
        <form className="cartao" onSubmit={enviar}>
          {origem && (
            <p className="selo" style={{ marginBottom: 16 }}>Usando o relatório “{origem.titulo}”</p>
          )}
          {def.campos.map((c) => (
            <CampoForm key={c.nome} campo={c} valor={valores[c.nome]}
                       mudar={(v) => setValores((atual) => ({ ...atual, [c.nome]: v }))} />
          ))}
          <button className="btn" style={{ width: "100%" }}>Gerar análise →</button>
          <p className="suave" style={{ fontSize: "0.82rem", marginTop: 10, textAlign: "center" }}>
            Leva de 1 a 3 minutos: a IA pesquisa na web e consulta a base antes de responder.
          </p>
        </form>
      )}

      {erro && <p className="erro">{erro}</p>}
      {status && <p className="status-vivo" role="status">{status}…</p>}
      {texto && (
        <article className="cartao" aria-busy={gerando}>
          <Markdown texto={texto} />
        </article>
      )}
      <Recomendacoes itens={recs} />
      <Fontes fontes={fontes} />

      {terminou && relatorioId && (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 24 }}>
          <Link href={`/app/relatorios/${relatorioId}`} className="btn">Abrir relatório salvo</Link>
          {def.modo !== "captar" && (
            <Link href={`/app/captar?origem=${relatorioId}`} className="btn btn-claro">Buscar investidores para isso →</Link>
          )}
        </div>
      )}
    </div>
  );
}

function CampoForm({ campo: c, valor, mudar }: { campo: Campo; valor: string | boolean; mudar: (v: string | boolean) => void }) {
  const id = `campo-${c.nome}`;
  if (c.tipo === "booleano") {
    return (
      <label className="campo-check" htmlFor={id}>
        <input id={id} type="checkbox" checked={Boolean(valor)} onChange={(e) => mudar(e.target.checked)} />
        <span>{c.rotulo}</span>
      </label>
    );
  }
  const comum = {
    id, required: c.obrigatorio, minLength: c.minimo, value: String(valor),
    placeholder: c.tipo === "area" ? undefined : c.dica,
  };
  return (
    <div className="campo">
      <label htmlFor={id}>{c.rotulo}{c.obrigatorio && " *"}</label>
      {c.tipo === "area" ? (
        <textarea {...comum} onChange={(e) => mudar(e.target.value)} />
      ) : c.tipo === "opcoes" ? (
        <select id={id} value={String(valor)} onChange={(e) => mudar(e.target.value)}>
          {c.opcoes!.map((o) => <option key={o.valor} value={o.valor}>{o.rotulo}</option>)}
        </select>
      ) : (
        <input {...comum} type="text" inputMode={c.tipo === "numero" ? "decimal" : undefined}
               onChange={(e) => mudar(e.target.value)} />
      )}
      {c.tipo === "area" && c.dica && <small>{c.dica}</small>}
    </div>
  );
}

export default function PaginaModo() {
  return (
    <Suspense>
      <Tela />
    </Suspense>
  );
}
