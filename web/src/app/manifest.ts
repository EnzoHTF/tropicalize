import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Tropicalize",
    short_name: "Tropicalize",
    description: "IA para empreender no Brasil: ideias, diagnóstico, validação e investidores.",
    lang: "pt-BR",
    start_url: "/app",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#FBF7EF",
    theme_color: "#0E3B2C",
    categories: ["business", "productivity", "news"],
    icons: [
      { src: "/icones/icone-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icones/icone-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icones/icone-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Validar ideia", url: "/app/validar" },
      { name: "Captar investimento", url: "/app/captar" },
      { name: "Notícias", url: "/blog" },
    ],
  };
}
