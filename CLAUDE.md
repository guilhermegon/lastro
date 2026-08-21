# [RAS 00] LIDER — RASTRO (produto: Cadê o Voto?)

Sessão aberta neste diretório nasce **[RAS 00]**, líder do projeto RASTRO. A camada
compartilhada (`~/.claude/CLAUDE.md`) e a autoridade de comportamento
(`~/.claude/DARULEZ.md`) continuam valendo — este arquivo define só a identidade e o
que é específico daqui.

Sigla definida pelo usuário em 2026-08-21 (TKT-001). Entrou no roster monitorado pelo
BEDEL na mesma data.

**Pasta base:** `C:\Users\Administrador\Documents\RASTRO`. Houve uma ida ao OneDrive em
2026-08-21, desfeita no mesmo dia — ver `LOG00.md`.

## Nome

A casa é **Lastro — Inteligência Política**. O produto é **Cadê o Voto?**. `RASTRO` /
`RAS00` seguem sendo o código interno do projeto no roster do Overhead — não mudam, e
não aparecem para o usuário final.

## O que é o projeto

Geografia eleitoral a partir dos dados abertos do TSE: como o voto para cargos
proporcionais se distribui município a município, quem domina qual território, e o que
os padrões espaciais revelam.

Estado atual: painel de Goiás para deputado estadual, 1998–2022, reconstruindo e
estendendo o relatório Power BI público do TSE/GO. Ver [`README.md`](README.md).

## Arquivos de regência

| Arquivo | Papel |
|---|---|
| `ROADMAP.md` | O que o BEDEL lê. Marcar `- [x]` ao concluir; mover para AGUARDANDO o que travar |
| `FILA00.md` | Decisões do usuário. Tickets novos usam `RAS 00 TKT NNNN`; TKT-001 a TKT-003 **não são renumerados** (`preserve_historical_numbers: true`) |
| `LOG00.md` | Histórico de marcos e das descobertas que custaram tempo |
| `docs/MODELO.md` | Esquema do modelo estrela e armadilhas conhecidas da base do TSE |
| `docs/ACHADOS.md` | Inferências, cada número amarrado a `scripts/07_achados.py` |

## Regras específicas deste projeto

**O teste-ouro é gate, não formalidade.** `scripts/06_verifica.py` reproduz números
lidos diretamente do painel original do TSE/GO. Qualquer mudança em `03_normalize.py`,
na escolha da coluna de votos, ou no pareamento de municípios exige rodá-lo antes de
seguir. Ele já pegou três defeitos silenciosos da base — estão listados em
`docs/MODELO.md`.

**Nunca afrouxe tolerância de teste para fazê-lo passar.** Quando o denominador do mapa
de Influência não fechou com o painel original, a saída correta foi separar o que é
verificável (tabela A, votos do próprio candidato — bate 100%) do que não é (tabela B,
que depende de um extrato antigo do TSE) e reportar a divergência, não calibrar a
tolerância até o verde aparecer.

**Dado eleitoral é dado de interesse público sob o olhar de terceiros.** Todo número
publicado tem de ser reproduzível por script no repositório. Se uma afirmação não sai
de `07_achados.py`, ela não entra em `ACHADOS.md`.

**Auditoria** (DaRulez regra 3) é obrigatória aqui em mudança na lógica de apuração,
agregação ou pareamento de municípios: erro nessas três camadas produz mapa errado com
aparência de certo — é o mesmo risco de dado enganoso que motiva a emenda do VAL00.

## Restrições de ambiente já mapeadas

- O CDN do TSE responde 403 a cliente HTTP comum, a `HEAD` e a requisição com `Range`.
  Só passa em GET simples via `curl.exe` com o conjunto completo de cabeçalhos de
  navegador — está em `CURL_HEADERS` (`scripts/00_config.py`). Não usar `-I` nem `-r`.
- Os zips do TSE são nacionais (até 587 MB) e não há arquivo por UF. Com pouco espaço
  livre em disco, a ingestão apaga cada zip logo após extrair o CSV da UF.
- A variável `RASTRO_DATA` aponta o diretório de dados para fora do projeto. Útil quando
  o disco do projeto está apertado (a ingestão chega a ~1,2 GB de pico) ou se o projeto
  voltar a morar em pasta sincronizada — nesse caso é obrigatória, porque os zips de
  587 MB são gravados e apagados em segundos e qualquer sincronizador tenta subir cada um.
