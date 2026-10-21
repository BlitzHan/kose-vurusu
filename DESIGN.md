# Design

World: **maç bileti** on a mown pitch. Operate surface, phone first.

## Tokens (assets/style.css `:root`)

| Role | Light | Dark |
|---|---|---|
| Pitch ground `--cim` / stripe `--cim-acik` / header `--cim-koyu` | #11562f / #146236 / #0b3f22 | #0b2f1b / #0d351f / #071f11 |
| Ticket stock `--bilet` / inset `--bilet-2` | #fbfbf6 / #f0f2ea | #e4e8df / #d6dbd1 |
| Ink `--murekkep` / 2 / 3 | #111612 / #465049 / #69736c | #0f1410 / #3a433d / #565f59 |
| Rules `--cizgi` / `--cizgi-koyu` | #d9ddd3 / #b9c0b5 | #c3c9be / #a7afa3 |
| Strong signal `--guclu` / tint | #127a3e / #dcefe1 | same / #c6e2cd |
| Result & change only `--sinyal` | #e5501a | same |
| Heat scale `--isi` | rgb 18,122,62 at alpha | same |

Dark keeps the ticket as dimmed paper on a darker pitch; it never inverts the ticket.

## Type

One family: **Archivo** (variable width 62–125, weight 400–900), tabular figures everywhere.
- Wordmark, day title: 850, width 125%.
- Team names: 850, width 112% (88% / 78% for long names), auto-fit so a word never breaks.
- Signal percentages: 850, width 112%; size encodes probability (`--p`: 60 → 30px, 90 → 46px).
- Labels: 11–12px, 700, uppercase, +0.05–0.08em tracking.
- Body: 15.5px / 1.45, max 60ch. Decimals with Turkish comma, percent as "%76".

## Components

- **Bilet**: `.govde` (band, teams, summary, signals, likely scores) + `.kocan` (stub). Half-moon edge notches via radial-gradient masks at the perforation; dotted tear line on the stub.
- **Signature move**: opening the stub separates it from the body by 12px (pitch shows through) with a one-shot tear wobble (`@keyframes yirt`); the drawer expands via `grid-template-rows`. Reduced motion: no wobble, no transitions.
- **Sinyal row**: big percentage, market name, tier tag (Güçlü filled green, Orta outlined), one evidence line (model · last 10 per team · market). After the match: orange "Tuttu" stamp or outlined "Tutmadı", missed row greyed.
- **No-signal state**: inset panel "Bu maçta güçlü sinyal yok" plus the closest market.
- **Drawer**: standard segmented tabs (Son maçlar, Oyuncular, Olasılıklar) and pill team toggle; tables with sticky first column, own value then small opponent value; player rows with last-5 rating cells tinted on the heat scale; absent players struck through in orange.
- **Finished band**: band turns `--sinyal` orange and shows the final score.

## Rules

- Orange is reserved for results and changes; green for signal strength; no other accents.
- No serif, no cream, no offset shadows; depth is one soft drop shadow on the ticket.
- Copy stays short: headline + one or two sentences per match.
