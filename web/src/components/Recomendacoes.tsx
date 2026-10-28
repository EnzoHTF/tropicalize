import type { Recomendacao } from "@/lib/api";

const TIPOS: Record<string, string> = {
  fundo_vc: "Fundo de VC", aceleradora: "Aceleradora", incubadora: "Incubadora", anjos: "Investidores-anjo",
  corporativo: "Corporativo", governo: "Governo / edital", programa: "Programa",
};

export default function Recomendacoes({ itens }: { itens: Recomendacao[] }) {
  if (!itens.length) return null;
  return (
    <section style={{ margin: "28px 0" }}>
      <h2 style={{ fontSize: "1.4rem", marginBottom: 12 }}>Onde se inscrever</h2>
      <div className="grade">
        {itens.map((r) => (
          <div key={r.investidor_id} className="cartao" style={{ padding: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "baseline" }}>
              <b>{r.nome}</b>
              <span className="selo">{r.aderencia}%</span>
            </div>
            <div className="suave" style={{ fontSize: "0.85rem", margin: "2px 0 8px" }}>
              {TIPOS[r.tipo] ?? r.tipo}
              {r.ticket_texto && ` · ${r.ticket_texto}`}
              {r.inscricao_fecha && ` · inscrições até ${new Date(r.inscricao_fecha + "T12:00").toLocaleDateString("pt-BR")}`}
            </div>
            <p style={{ fontSize: "0.93rem", marginBottom: 12 }}>{r.motivo}</p>
            {r.url_inscricao && (
              <a href={r.url_inscricao} target="_blank" rel="noopener noreferrer" className="btn btn-pequeno">
                Ver inscrição →
              </a>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
