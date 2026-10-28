# Cockpit triathlon – Canyon Speedmax CF (v0.5)

Ricostruzione parametrica da foto + video a 360°. Quote stimate: **stampare prima `P0_test_clip`**.

Forma v0.5: vasca a barca a cuneo (pareti basse in punta che salgono lineari fino a ~80 mm in coda, svasate 22°, retro aperto), due lobi convessi che partono sui tubi e divergono verso il retro (centro ±35 → ±72 mm, larghi 30 → 56 mm),
carenature cilindriche delle estensioni visibili nel canale, blocco posteriore largo 72 mm, dorsale a chiglia sotto il fondo (più profonda verso il retro) con le sedi a scatto. Tubi punta piegati di 60°, il tratto dritto entra per 40 mm nel muso.

## Prima di stampare
1. Misura sulla bici l'**interasse delle estensioni** (asse–asse) → `ext_cc` in `cockpit.py` (default 70).
2. Rigenera: `python cockpit.py` (serve CadQuery) → file in `out/`; poi `python drawings.py` per i disegni tecnici del visualizzatore (`viewer/draw/`).
3. Stampa `P0_test_clip` (15 g, ~30 min) e prova l'aggancio:
   - entra troppo duro / si crepa → aumenta `clip_open` (19 → 19.5) o `fit`
   - balla → riduci `fit` (0.25 → 0.15)

## Parti (`out/`, STEP + STL)
| File | Q.tà | Orientamento su X1C |
|---|---|---|
| P1_vassoio_anteriore | 1 | in piedi sulla faccia di taglio (Y=180) → nessun supporto sotto le ali |
| P2_vassoio_posteriore | 1 | in piedi sulla faccia di taglio |
| P3_tubo_punta_dx / sx | 1+1 | verticali, punta in alto |
| P4_colonnina_computer | 1 | verticale |
| P5_braccio_borraccia | 1 | piatto, sedi dadi in basso |

Tutte stanno nel volume 256³ (pezzo più largo 247 mm).

## Impostazioni consigliate
- Materiale: **PETG** (o ASA se sta al sole). PA-CF se vuoi rigidità massima.
- 4 pareti, 5 top/bottom, gyroid 20 %, layer 0.2.
- Cerniera e tubi: 6 pareti.

## Minuteria
- 2× M5×16 svasate + 2× inserto a caldo M5 (braccio borraccia fisso, sul blocco posteriore inclinato 25°)
- 2× M5×12 + dadi (gabbia, fori 64 mm)
- 1× M5×30 + dado (colonnina computer, 3 posizioni; dado nella sede esagonale sotto la dorsale)
- 2× M3×8 (puck computer, fori 20 mm – verifica sul tuo puck)
- 2× inserto a caldo M4 + grano M4×6 (tubi punta)
- 2× spina Ø4×24 nella dorsale + colla epossidica (giunzione metà)

## Montaggio
1. Incolla P1+P2 con le spine.
2. Infila i tubi punta P3 nelle sedi del muso (40 mm), poi le estensioni dentro i tubi; blocca con grano.
3. Clip a scatto sulle estensioni per tutta la lunghezza.
4. Shifter Shimano nella punta dei P3 (foro Ø21.6 = `shifter_d`; sede estensione Ø22.7 per 41 mm).

## Limiti noti
- Geometria da foto: proporzioni ±10–15 %.
- Interasse estensioni Speedmax CF non trovato online → va misurato.
- Funzione asole quadrate posteriori ignota → modellate come passanti cinghia velcro.
- Interfaccia puck computer generica (2× M3).
