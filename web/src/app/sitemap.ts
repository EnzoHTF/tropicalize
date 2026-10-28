import type { MetadataRoute } from "next";
import { noticiasPublicas } from "@/lib/blog";
import { SITE_URL } from "@/lib/config";

export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const noticias = await noticiasPublicas();
  return [
    { url: SITE_URL, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE_URL}/blog`, changeFrequency: "hourly", priority: 0.8 },
    ...noticias.map((n) => ({ url: `${SITE_URL}/blog/${n.slug}`, lastModified: n.publicado_em, priority: 0.6 })),
  ];
}
