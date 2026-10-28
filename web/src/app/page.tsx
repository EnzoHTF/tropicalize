import Link from "next/link";
import Topo from "@/components/Topo";
import { noticiasPublicas } from "@/lib/blog";
import { MODOS } from "@/lib/modos";
import s from "./inicio.module.css";

export const revalidate = 600;

export default async function Inicio() {
  const noticias = (await noticiasPublicas()).slice(0, 3);

  return (
    <>
      <div className="wrap">
        <Topo />
        <header className={s.hero}>
          <span className="selo">Startups da Y Combinator e do F6S + fundos, aceleradoras e editais</span>
          <h1>
            A IA para quem quer empreender e para quem <em>já empreende</em> no Brasil
          </h1>
          <p className={s.sub}>
            Importe ideias que já deram certo lá fora, descubra os gargalos da sua empresa, valide e viabilize sua
            ideia com as ferramentas certas para o seu orçamento e encontre investidores para se inscrever.
          </p>
          <div className={s.acoes}>
            <Link href="/app" className="btn">Começar grátis →</Link>
            <Link href="/blog" className="btn btn-claro">Ler as notícias</Link>
          </div>
        </header>
      </div>

      <section className={s.secao} id="modos">
        <div className="wrap">
          <h2 className={s.tituloSecao}>Quatro jeitos de usar</h2>
          <p className={s.descSecao}>Escolha o seu momento. Cada análise vira um relatório salvo, que você pode levar para o próximo passo.</p>
          <div className={s.modos}>
            {MODOS.map((m) => (
              <Link key={m.modo} href={`/app/${m.modo}`} className={`cartao ${s.modo}`}>
                <span className={s.icone} aria-hidden>{m.icone}</span>
                <small>{m.chamada}</small>
                <h3>{m.titulo}</h3>
                <p>{m.descricao}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className={s.secao}>
        <div className="wrap">
          <div className={s.faixa}>
            <div>
              <h2>Respostas com fonte, não achismo</h2>
              <p>
                A IA só cita startups, investidores e ferramentas da nossa base ou de pesquisas na web feitas na hora,
                sempre com link. Quando faltar dado, ela diz.
              </p>
              <Link href="/app" className="btn btn-sol">Fazer minha primeira análise →</Link>
            </div>
            <div className={s.blocos}>
              <div className={s.bloco}><b>Benchmarks reais</b><span>Milhares de startups da Y Combinator e programas do F6S.</span></div>
              <div className={s.bloco}><b>Investidores e editais</b><span>Fundos de VC, aceleradoras, anjos e capital não diluitivo, com prazos.</span></div>
              <div className={s.bloco}><b>Olhar de investidor</b><span>Nota, análise de mercado e crítica no padrão de um VC.</span></div>
              <div className={s.bloco}><b>Alertas de prazo</b><span>Aviso no celular antes de fechar a inscrição recomendada para você.</span></div>
            </div>
          </div>
        </div>
      </section>

      {noticias.length > 0 && (
        <section className={s.secao}>
          <div className="wrap">
            <h2 className={s.tituloSecao}>Notícias de negócios e venture capital</h2>
            <p className={s.descSecao}>O que está acontecendo no Brasil e no mundo, resumido para quem empreende.</p>
            <div className={s.noticias}>
              {noticias.map((n) => (
                <Link key={n.id} href={`/blog/${n.slug}`} className={`cartao ${s.noticia}`}>
                  <span className="selo">{n.categoria === "brasil" ? "Brasil" : "Mundo"}</span>
                  <h3>{n.titulo}</h3>
                  <p>{n.resumo.slice(0, 140)}…</p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      <div className="wrap">
        <footer className="rodape">
          <span>© {new Date().getFullYear()} Tropicalize</span>
          <span>Dados públicos (Y Combinator, F6S, sites oficiais). Não é recomendação de investimento.</span>
        </footer>
      </div>
    </>
  );
}
