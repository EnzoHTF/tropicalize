"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Topo from "@/components/Topo";
import { api, type Eu } from "@/lib/api";
import type { Noticia } from "@/lib/blog";
import { useSessao } from "@/lib/supabase";

type Post = { rede: string; texto: string; status: string };
type Rascunho = Noticia & { posts: Post[]; status: string };
type Newsletter = { id: number; newsletter_semana: string; texto: string; status: string };

const REDES = ["instagram", "linkedin", "x", "threads"];

/** Curadoria: nada vai ao ar (blog e redes) sem aprovação humana. */
export default function Admin() {
  const sessao = useSessao();
  const router = useRouter();
  const [eu, setEu] = useState<Eu | null>(null);
  const [fila, setFila] = useState<Rascunho[]>([]);
  const [newsletters, setNewsletters] = useState<Newsletter[]>([]);
  const [aviso, setAviso] = useState("");

  const carregar = useCallback(() => {
    api<Rascunho[]>("/api/admin/noticias").then(setFila).catch(() => {});
    api<Newsletter[]>("/api/admin/newsletter").then(setNewsletters).catch(() => {});
  }, []);

  useEffect(() => {
    if (sessao === null) router.replace("/entrar?volta=/admin");
    if (sessao) api<Eu>("/api/eu").then((e) => { setEu(e); if (e.admin) carregar(); });
  }, [sessao, router, carregar]);

  if (!eu) return <div className="wrap"><Topo direita={<span />} /><p className="status-vivo">Carregando</p></div>;
  if (!eu.admin) return <div className="wrap"><Topo /><p className="erro">Acesso restrito à equipe.</p></div>;

  const atualizar = (id: number, mudanca: Partial<Rascunho>) =>
    setFila((f) => f.map((n) => (n.id === id ? { ...n, ...mudanca } : n)));

  async function publicar(n: Rascunho) {
    await api(`/api/admin/noticias/${n.id}`, {
      method: "PUT",
      body: JSON.stringify({ titulo: n.titulo, resumo: n.resumo, por_que_importa: n.por_que_importa,
                             posts: Object.fromEntries(n.posts.map((p) => [p.rede, p.texto])) }),
    });
    const r = await api<{ posts_enviados: number }>(`/api/admin/noticias/${n.id}/publicar`, { method: "POST" });
    setAviso(`Publicada. Posts enviados às redes: ${r.posts_enviados}.`);
    setFila((f) => f.filter((x) => x.id !== n.id));
  }

  async function descartar(id: number) {
    await api(`/api/admin/noticias/${id}/descartar`, { method: "POST" });
    setFila((f) => f.filter((x) => x.id !== id));
  }

  async function coletar() {
    setAviso("Coletando notícias…");
    const r = await api<{ novas: number }>("/api/admin/coletar-noticias", { method: "POST" });
    setAviso(`${r.novas} notícias novas na fila.`);
    carregar();
  }

  async function gerarNewsletter() {
    setAviso("Gerando a newsletter da semana…");
    await api("/api/admin/newsletter", { method: "POST" });
    setAviso("Newsletter gerada.");
    carregar();
  }

  return (
    <div className="wrap">
      <Topo direita={<Link href="/app">Voltar ao app</Link>} />
      <main style={{ paddingBottom: 64 }}>
        <h1 style={{ fontSize: "1.9rem", marginBottom: 12 }}>Curadoria de notícias</h1>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
          <button className="btn btn-pequeno" onClick={coletar}>Coletar agora</button>
          <button className="btn btn-claro btn-pequeno" onClick={gerarNewsletter}>Gerar newsletter da semana</button>
        </div>
        {aviso && <p className="selo" style={{ marginBottom: 16 }}>{aviso}</p>}

        {fila.length === 0 && <p className="suave">Nenhum rascunho na fila.</p>}
        <div style={{ display: "grid", gap: 16 }}>
          {fila.map((n) => (
            <article key={n.id} className="cartao">
              <div className="suave" style={{ fontSize: "0.82rem" }}>
                {n.categoria} · <a href={n.fonte_url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--folha)" }}>{n.fonte_nome}</a>
              </div>
              <div className="campo"><label>Título</label>
                <input value={n.titulo} onChange={(e) => atualizar(n.id, { titulo: e.target.value })} /></div>
              <div className="campo"><label>Resumo (markdown)</label>
                <textarea rows={6} value={n.resumo} onChange={(e) => atualizar(n.id, { resumo: e.target.value })} /></div>
              <div className="campo"><label>Por que importa</label>
                <textarea rows={3} value={n.por_que_importa ?? ""} onChange={(e) => atualizar(n.id, { por_que_importa: e.target.value })} /></div>
              <details>
                <summary style={{ cursor: "pointer", fontWeight: 600, marginBottom: 10 }}>Posts para redes sociais</summary>
                {REDES.map((rede) => {
                  const post = n.posts.find((p) => p.rede === rede);
                  if (!post) return null;
                  return (
                    <div className="campo" key={rede}><label>{rede}</label>
                      <textarea rows={4} value={post.texto}
                        onChange={(e) => atualizar(n.id, { posts: n.posts.map((p) => (p.rede === rede ? { ...p, texto: e.target.value } : p)) })} />
                    </div>
                  );
                })}
              </details>
              <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
                <button className="btn btn-pequeno" onClick={() => publicar(n)}>Publicar</button>
                <button className="btn btn-claro btn-pequeno" onClick={() => descartar(n.id)}>Descartar</button>
              </div>
            </article>
          ))}
        </div>

        {newsletters.length > 0 && (
          <section style={{ marginTop: 40 }}>
            <h2 style={{ fontSize: "1.4rem", marginBottom: 12 }}>Newsletters</h2>
            {newsletters.map((nl) => (
              <details key={nl.id} className="cartao" style={{ marginBottom: 10 }}>
                <summary style={{ cursor: "pointer", fontWeight: 600 }}>Semana de {new Date(nl.newsletter_semana + "T12:00").toLocaleDateString("pt-BR")}</summary>
                <textarea readOnly rows={14} value={nl.texto} style={{ width: "100%", marginTop: 10, padding: 12, borderRadius: 12, border: "1px solid var(--borda)", background: "var(--card)" }} />
                <button className="btn btn-pequeno" style={{ marginTop: 8 }} onClick={() => navigator.clipboard.writeText(nl.texto)}>Copiar</button>
              </details>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
