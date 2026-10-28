import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import Markdown from "@/components/Markdown";
import Topo from "@/components/Topo";
import { noticiaPublica } from "@/lib/blog";
import { SITE_URL } from "@/lib/config";

export const revalidate = 300;

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const n = await noticiaPublica((await params).slug);
  if (!n) return { title: "Notícia não encontrada" };
  const descricao = n.resumo.replace(/\s+/g, " ").slice(0, 160);
  return {
    title: n.titulo,
    description: descricao,
    alternates: { canonical: `/blog/${n.slug}` },
    openGraph: { type: "article", title: n.titulo, description: descricao, publishedTime: n.publicado_em, tags: n.tags },
    twitter: { card: "summary_large_image", title: n.titulo, description: descricao },
  };
}

export default async function Noticia({ params }: Props) {
  const n = await noticiaPublica((await params).slug);
  if (!n) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    headline: n.titulo,
    datePublished: n.publicado_em,
    inLanguage: "pt-BR",
    mainEntityOfPage: `${SITE_URL}/blog/${n.slug}`,
    publisher: { "@type": "Organization", name: "Tropicalize", logo: { "@type": "ImageObject", url: `${SITE_URL}/icones/icone-512.png` } },
    isBasedOn: n.fonte_url,
  };

  return (
    <div className="wrap">
      <Topo />
      <main className="wrap-estreito" style={{ padding: "8px 0 48px" }}>
        <Link href="/blog" className="suave" style={{ fontSize: "0.9rem" }}>← Notícias</Link>
        <div className="suave" style={{ fontSize: "0.85rem", margin: "14px 0 6px" }}>
          <span className="selo">{n.categoria === "brasil" ? "Brasil" : "Mundo"}</span>{" "}
          {new Date(n.publicado_em).toLocaleDateString("pt-BR")}
        </div>
        <h1 style={{ fontSize: "clamp(1.7rem, 5vw, 2.4rem)", marginBottom: 20 }}>{n.titulo}</h1>
        <Markdown texto={n.resumo} />
        {n.por_que_importa && (
          <aside className="cartao" style={{ margin: "24px 0", borderLeft: "4px solid var(--folha)" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: 6 }}>Por que isso importa para quem empreende</h2>
            <p>{n.por_que_importa}</p>
          </aside>
        )}
        <p className="suave" style={{ fontSize: "0.9rem" }}>
          Fonte original:{" "}
          <a href={n.fonte_url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--folha)" }}>
            {n.fonte_nome}
          </a>
        </p>
        <div className="cartao" style={{ marginTop: 32, textAlign: "center" }}>
          <h2 style={{ fontSize: "1.25rem", marginBottom: 6 }}>Tem uma ideia nessa área?</h2>
          <p className="suave" style={{ marginBottom: 14 }}>Valide o potencial e descubra fundos e aceleradoras para se inscrever.</p>
          <Link href="/app/validar" className="btn">Analisar minha ideia →</Link>
        </div>
      </main>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
    </div>
  );
}
