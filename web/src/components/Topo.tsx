import Link from "next/link";

export default function Topo({ direita }: { direita?: React.ReactNode }) {
  return (
    <nav className="topo">
      <Link href="/" className="marca">
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG pequeno, sem ganho com next/image */}
        <img src="/logo.svg" alt="" />
        tropicalize
      </Link>
      <div className="topo-links">
        <Link href="/blog" className="so-desktop">Notícias</Link>
        {direita ?? (
          <Link href="/app" className="btn btn-claro btn-pequeno">
            Entrar
          </Link>
        )}
      </div>
    </nav>
  );
}
