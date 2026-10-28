/** Leitura pública do blog, feita no servidor com cache do Next. */
import { API_URL } from "./config";

export type Noticia = {
  id: number;
  slug: string;
  titulo: string;
  resumo: string;
  categoria: "brasil" | "mundo";
  tags: string[];
  fonte_nome: string;
  imagem_url: string | null;
  publicado_em: string;
  por_que_importa?: string;
  fonte_url?: string;
};

/** Leitura pública do blog (usada no servidor, com cache do Next). */
export async function noticiasPublicas(params = ""): Promise<Noticia[]> {
  try {
    const r = await fetch(`${API_URL}/api/noticias${params}`, { next: { revalidate: 300 } });
    return r.ok ? r.json() : [];
  } catch {
    return [];
  }
}

export async function noticiaPublica(slug: string): Promise<Noticia | null> {
  try {
    const r = await fetch(`${API_URL}/api/noticias/${encodeURIComponent(slug)}`, { next: { revalidate: 300 } });
    return r.ok ? r.json() : null;
  } catch {
    return null;
  }
}
