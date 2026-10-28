"use client";

import { ehNativo } from "./push";

/** Compartilha o texto pela folha nativa (app ou navegador) ou copia para a área de transferência. */
export async function compartilhar(titulo: string, texto: string) {
  const conteudo = `${titulo}\n\n${texto}\n\nGerado no Tropicalize`;
  if (ehNativo()) {
    const { Share } = await import("@capacitor/share");
    await Share.share({ title: titulo, text: conteudo });
  } else if (navigator.share) {
    await navigator.share({ title: titulo, text: conteudo }).catch(() => {});
  } else {
    await navigator.clipboard.writeText(conteudo);
    alert("Relatório copiado para a área de transferência.");
  }
}
