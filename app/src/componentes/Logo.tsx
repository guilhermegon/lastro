/** Marca Lastro. As cores vêm dos tokens, então acompanha o tema sozinha. */
export function Logo() {
  return (
    <span className="lastro" role="img" aria-label="Lastro — Inteligência Política">
      <svg viewBox="0 0 260 68" aria-hidden="true" focusable="false">
        <g className="lastro-mark">
          <rect x="12" y="12" width="4" height="44" rx="1" />
          <rect x="21" y="12" width="16" height="4" rx="1.5" opacity=".42" />
          <rect x="21" y="24" width="26" height="6" rx="2" opacity=".66" />
          <rect x="21" y="38" width="38" height="8" rx="2.5" />
          <rect x="12" y="52" width="52" height="4" rx="1.5" />
        </g>
        <text className="lastro-nome" x="82" y="36">LASTRO</text>
        <text className="lastro-sub" x="83.5" y="52">INTELIGÊNCIA POLÍTICA</text>
      </svg>
    </span>
  );
}
