import type { Metadata } from "next";
import Link from "next/link";
import Topo from "@/components/Topo";
import { noticiasPublicas } from "@/lib/blog";

export const revalidate = 300;

export const metadata: Metadata = {
  title: "Notícias de startups, venture capital e negócios",
  description: "As principais notícias do Brasil e do mundo sobre startups, venture capital e negócios, resumidas para quem empreende.",
  alternates: { canonical: "/blog" },
};

const ABAS = [
  { valor: undefined, rotulo: "Tudo" },
  { valor: "brasil", rotulo: "Brasil" },
  { valor: "mundo", rotulo: "Mundo" },
] as const;

export default async function Blog({ searchParams }: { searchParams: Promise<{ categoria?: string; pagina?: string }> }) {
  const { categoria, pagina } = await searchParams;
  const cat = categoria === "brasil" || categoria === "mundo" ? categoria : undefined;
  const pag = Math.max(Number(pagina) || 1, 1);
  const params = new URLSearchParams({ pagina: String(pag), ...(cat ? { categoria: cat } : {}) });
  const noticias = await noticiasPublicas(`?${params}`);

  return (
    <div className="wrap">
      <Topo />
      <main className="wrap-estreito" style={{ padding: "8px 0 48px" }}>
        <h1 style={{ fontSize: "clamp(1.8rem, 5vw, 2.6rem)", marginBottom: 8 }}>Notícias</h1>
        <p className="suave" style={{ marginBottom: 20 }}>Startups, venture capital e negócios no Brasil e no mundo, com o que isso significa para quem empreende.</p>
        <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
          {ABAS.map((a) => (
            <Link key={a.rotulo} href={a.valor ? `/blog?categoria=${a.valor}` : "/blog"}
                  className={`btn btn-pequeno ${cat === a.valor ? "" : "btn-claro"}`}>
              {a.rotulo}
            </Link>
          ))}
        </div>
        <div style={{ display: "grid", gap: 14 }}>
          {noticias.map((n) => (
            <Link key={n.id} href={`/blog/${n.slug}`} className="cartao" style={{ padding: 20 }}>
              <div className="suave" style={{ fontSize: "0.82rem", marginBottom: 4 }}>
                <span className="selo">{n.categoria === "brasil" ? "Brasil" : "Mundo"}</span>{" "}
                {new Date(n.publicado_em).toLocaleDateString("pt-BR")} · via {n.fonte_nome}
              </div>
              <h2 style={{ fontSize: "1.2rem", margin: "6px 0" }}>{n.titulo}</h2>
              <p className="suave" style={{ fontSize: "0.95rem" }}>{n.resumo.slice(0, 220)}…</p>
            </Link>
          ))}
          {!noticias.length && <p className="suave">Nenhuma notícia por aqui ainda.</p>}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
          {pag > 1 ? <Link className="btn btn-claro btn-pequeno" href={`/blog?${new URLSearchParams({ ...(cat ? { categoria: cat } : {}), pagina: String(pag - 1) })}`}>← Anteriores</Link> : <span />}
          {noticias.length === 20 && <Link className="btn btn-claro btn-pequeno" href={`/blog?${new URLSearchParams({ ...(cat ? { categoria: cat } : {}), pagina: String(pag + 1) })}`}>Mais antigas →</Link>}
        </div>
      </main>
    </div>
  );
}
