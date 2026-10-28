import { ImageResponse } from "next/og";
import { noticiaPublica } from "@/lib/blog";

// Card usado nas redes sociais e na prévia de links (1200x630)
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Notícia do Tropicalize";

export default async function Imagem({ params }: { params: Promise<{ slug: string }> }) {
  const n = await noticiaPublica((await params).slug);
  const titulo = n?.titulo ?? "Tropicalize";
  const categoria = n?.categoria === "mundo" ? "MUNDO" : "BRASIL";

  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between",
                    background: "#0E3B2C", color: "#fff", padding: "64px 72px", fontFamily: "sans-serif" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: "#35B37A", display: "flex" }} />
          <span style={{ fontSize: 36, fontWeight: 700 }}>tropicalize</span>
          <span style={{ marginLeft: "auto", fontSize: 24, color: "#F4B740", letterSpacing: 2 }}>{categoria}</span>
        </div>
        <div style={{ fontSize: titulo.length > 70 ? 54 : 64, fontWeight: 700, lineHeight: 1.12, display: "flex" }}>{titulo}</div>
        <div style={{ fontSize: 26, color: "rgba(255,255,255,.75)", display: "flex" }}>
          Startups, venture capital e negócios para quem empreende no Brasil
        </div>
      </div>
    ),
    size,
  );
}
