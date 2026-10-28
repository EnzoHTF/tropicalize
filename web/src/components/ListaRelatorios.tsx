import Link from "next/link";
import type { Relatorio } from "@/lib/api";

export type Resumo = Pick<Relatorio, "id" | "modo" | "titulo" | "status" | "criado_em">;

export default function ListaRelatorios({ itens }: { itens: Resumo[] }) {
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {itens.map((r) => (
        <Link key={r.id} href={`/app/relatorios/${r.id}`} className="cartao" style={{ padding: "14px 18px" }}>
          <b>{r.titulo}</b>
          <div className="suave" style={{ fontSize: "0.85rem" }}>
            {new Date(r.criado_em).toLocaleDateString("pt-BR")}
            {r.status === "gerando" && " · gerando…"}
            {r.status === "erro" && " · não terminou"}
          </div>
        </Link>
      ))}
    </div>
  );
}
