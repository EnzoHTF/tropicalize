// Gera os ícones PNG da PWA e das lojas a partir de public/logo.svg (usa o sharp que vem com o Next).
import sharp from "sharp";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const svg = await readFile(new URL("../public/logo.svg", import.meta.url));
const saida = (nome) => fileURLToPath(new URL(`../public/icones/${nome}`, import.meta.url));

for (const tamanho of [192, 512, 1024]) {
  await sharp(svg, { density: 512 }).resize(tamanho, tamanho).png().toFile(saida(`icone-${tamanho}.png`));
}
await sharp(svg, { density: 512 }).resize(180, 180).flatten({ background: "#0E3B2C" }).png().toFile(saida("apple-touch-icon.png"));
// Maskable: logo com margem de segurança sobre o fundo da marca
const miolo = await sharp(svg, { density: 512 }).resize(360, 360).png().toBuffer();
await sharp({ create: { width: 512, height: 512, channels: 4, background: "#0E3B2C" } })
  .composite([{ input: miolo, gravity: "center" }]).png().toFile(saida("icone-maskable-512.png"));
console.log("ícones gerados em public/icones");
