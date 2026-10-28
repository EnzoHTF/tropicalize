import { noticiasPublicas } from "@/lib/blog";
import { SITE_URL } from "@/lib/config";

export const revalidate = 300;

const escapar = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** RSS do blog: serve para leitores de feed e para automações de redes sociais. */
export async function GET() {
  const noticias = await noticiasPublicas();
  const itens = noticias
    .map((n) => {
      const link = `${SITE_URL}/blog/${n.slug}`;
      return `<item><title>${escapar(n.titulo)}</title><link>${link}</link><guid>${link}</guid>` +
        `<pubDate>${new Date(n.publicado_em).toUTCString()}</pubDate><category>${n.categoria}</category>` +
        `<description>${escapar(n.resumo)}</description></item>`;
    })
    .join("");
  const xml = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>` +
    `<title>Tropicalize · Notícias</title><link>${SITE_URL}/blog</link><language>pt-BR</language>` +
    `<description>Startups, venture capital e negócios para quem empreende no Brasil</description>${itens}</channel></rss>`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } });
}
