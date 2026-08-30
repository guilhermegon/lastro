import { useMemo, type ReactNode } from "react";
import { projetar } from "../lib/projecao";
import { MarcaCapital } from "./MarcaCapital";
import type { GeometriaMunicipio, Zonas } from "../tipos";
import type { EstadoDica } from "./Dica";

/**
 * As zonas eleitorais do estado, desenhadas com a malha municipal.
 *
 * **A zona não cabe dentro do município: ela contém municípios.** Em Goiás, 68
 * das 92 zonas cobrem mais de um — a zona 8 cobre oito — e 242 dos 246
 * municípios pertencem a uma zona só. Por isso a zona é desenhável sem
 * inventar nada: onde todos os seus municípios são exclusivos dela, a
 * fronteira da zona É a soma de fronteiras municipais que o IBGE já publicou.
 * São 75 das 92.
 *
 * **As outras 17 não têm área, e o mapa não finge que têm.** Elas vivem dentro
 * de Goiânia, Anápolis, Aparecida e Rio Verde — cidades que sozinhas contêm
 * várias zonas. Ali a divisão existe por seção eleitoral, e não há fronteira
 * publicada; esses quatro municípios saem hachurados, e quem quiser ver zona
 * neles usa o mapa de urnas, onde cada local de votação traz a sua.
 *
 * **A cor não identifica a zona — só separa uma da outra.** Noventa e duas
 * categorias nominais não têm paleta possível, e a saída é a dos mapas
 * políticos desde sempre: colorir de modo que zonas vizinhas nunca partilhem
 * cor. Bastam cinco (`56_zonas_uf.py` calcula e avisa se passar de seis). Quem
 * identifica é o rótulo, no toque.
 */
export function MapaZonas({ geo, municipios, zonas, idx, capital,
                            aoInspecionar }: {
  geo: (GeometriaMunicipio | null)[];
  municipios: { n: string }[];
  zonas: Zonas;
  /** índice do município aberto, ou -1 */
  idx: number;
  /** a capital do estado, apontada e nomeada como em todo mapa de estado */
  capital?: { i: number; nome: string };
  aoInspecionar: (d: EstadoDica | null) => void;
}) {
  const { caminhos, pontos, largura, altura } = useMemo(() => projetar(geo), [geo]);
  const pCap = capital ? pontos[capital.i] : null;

  const emFoco = useMemo(() => {
    const zs = new Set(zonas.porMun[idx] ?? []);
    if (!zs.size) return null;
    const mun = new Set<number>();
    zonas.zonas.forEach((z) => {
      if (zs.has(z.z)) z.mi.forEach((i) => mun.add(i));
    });
    return { zs, mun };
  }, [zonas, idx]);

  const nomeZona = (i: number) => {
    const zs = zonas.porMun[i] ?? [];
    if (!zs.length) return "sem zona";
    return zs.length === 1 ? `zona ${zs[0]}` : `zonas ${zs.join(", ")}`;
  };

  return (
    <svg viewBox={`0 0 ${largura} ${altura}`} role="img"
         aria-label="Zonas eleitorais do estado"
         style={{ width: "100%", height: "auto", display: "block" }}>
      <defs>
        {/* Hachura para o município que contém mais de uma zona: ele não tem
            UMA cor, e pintá-lo com qualquer uma afirmaria uma zona que só
            cobre parte dele. */}
        <pattern id="zona-partida" width="6" height="6"
                 patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="6" height="6" fill="var(--surface-2)" />
          <rect width="2" height="6" fill="var(--line-strong)" />
        </pattern>
      </defs>
      {caminhos.map((d, i) => {
        if (!d) return null;
        const zs = zonas.porMun[i] ?? [];
        const partido = zs.length > 1;
        const z = zonas.zonas.find((x) => x.z === zs[0]);
        const cor = partido || z?.cor == null
          ? "url(#zona-partida)"
          : `var(--z${z.cor + 1})`;
        const dentro = !emFoco || emFoco.mun.has(i);
        return (
          <path
            key={i}
            d={d}
            className="mun"
            fill={cor}
            fillOpacity={dentro ? 0.85 : 0.13}
            stroke={i === idx ? "var(--ink)" : "var(--surface)"}
            strokeWidth={i === idx ? 1.8 : 0.5}
            onMouseMove={(e) => aoInspecionar({
              x: e.clientX, y: e.clientY,
              conteudo: (
                <>
                  <strong>{municipios[i]?.n}</strong>
                  {nomeZona(i)}
                  {partido && <><br />o município tem mais de uma zona</>}
                </>
              ) as ReactNode,
            })}
            onMouseLeave={() => aoInspecionar(null)}
            onTouchStart={(e) => {
              const t = e.touches[0];
              if (t) aoInspecionar({
                x: t.clientX, y: t.clientY,
                conteudo: <><strong>{municipios[i]?.n}</strong>{nomeZona(i)}</>,
              });
            }}
          />
        );
      })}
      {pCap && capital && (
        <MarcaCapital p={pCap} nome={capital.nome} largura={largura} />
      )}
    </svg>
  );
}
