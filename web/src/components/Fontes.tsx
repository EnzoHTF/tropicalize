export default function Fontes({ fontes }: { fontes: { titulo: string; url: string }[] }) {
  if (!fontes.length) return null;
  return (
    <details className="cartao" style={{ padding: "14px 18px", marginTop: 24 }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>Fontes pesquisadas na web ({fontes.length})</summary>
      <ul style={{ paddingLeft: 20, marginTop: 10, fontSize: "0.9rem" }}>
        {fontes.map((f) => (
          <li key={f.url}>
            <a href={f.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--folha)" }}>
              {f.titulo || f.url}
            </a>
          </li>
        ))}
      </ul>
    </details>
  );
}
