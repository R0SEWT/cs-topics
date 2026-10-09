# Diapositivas del TB1 (Quarto + reveal.js + D3)

En línea: <https://kenken.rosewt.dev> (Netlify, sitio `kenken-tb1`; el DNS de `rosewt.dev` vive en Netlify).

`index.qmd` es la exposición del TB1, «¿Qué sobrevive a una lectura equivocada?»: 22
diapositivas y un apéndice con limitaciones, la comparación de OCR y los tiempos. Sigue el
hilo del informe (`../informe/main.pdf`) con la misma familia visual del deck de Jev.

Ninguna cifra de los gráficos está escrita a mano. `datos/` lo genera un script a partir de
una foto real y de los 70 tableros con verdad:

```bash
cd labs/tb1-kenken
PYTHONPATH=. uv run python scripts/datos_diapos.py FOTO data_scraped/extraidos ../../presentacion/datos
```

`FOTO` es la que tomamos con el celular a la pantalla
(`dataset_fotografico/fotos/foto_20261008_230322_196526.jpg`, también en el dataset de
Hugging Face). Solo las barras del conjunto sintético copian la tabla del informe.

## Ver y presentar

```bash
cd presentacion
quarto preview index.qmd
```

| Tecla | Qué hace |
|---|---|
| `S` | Vista del orador, con las notas: quién habla y qué decir |
| `C` / `B` | Pizarra sobre la diapositiva / pizarra en blanco |
| `M` | Menú con todas las diapositivas |
| `F` | Pantalla completa |

Reparto propuesto en las notas: Rody abre y cuenta el solver y la reparación; Jorge, la
Fase 1 y la app; José, los datos y la lectura de etiquetas. La demo en vivo necesita el
nodo levantado y `adb reverse tcp:8723 tcp:8723`; `scrcpy` refleja el celular en la laptop.

## Un solo archivo, sin servidor

```bash
quarto render index.qmd --profile autonomo
```

Deja `_site/TB1-KenKen-diapositivas.html` (~9 MB), con imágenes, datos y D3 adentro, para
adjuntarlo al release. Ese perfil apaga la pizarra (no admite un solo archivo) y cambia la
celda OJS de la reparación por el mismo control en JS, porque Quarto no ejecuta OJS desde
`file://`.

## Publicar en Netlify

```bash
quarto render index.qmd && quarto render index.qmd --profile autonomo
npx netlify-cli deploy --prod --no-build --dir _site --site bb637f31-313c-4159-aa95-e771143dd00a
```

La raíz sirve la versión con pizarra y OJS; `/TB1-KenKen-diapositivas.html` es el archivo
único.

## Qué usa de Quarto y D3

- **D3 por pasos**: cada fragmento avanza un gráfico (`js/viz.js`). La lista numerada al
  lado narra el mismo paso, también al retroceder.
- **Una foto real de punta a punta**: umbral, homografía, periodicidad de la rejilla,
  grosor de aristas y la reparación de los dos 3÷ dibujada sobre la foto con la homografía
  inversa.
- **Unidades**: las 895 etiquetas (waffle) y los 70 tableros, que se reagrupan según lo que
  hizo el sistema con cada uno.
- **OJS**: la regla del margen, interactiva, sobre las 19 lecturas reales sin solución.
- **Interacción directa**: elegir n en la rejilla; pasar el mouse por el histograma de
  grosores marca sus aristas en el tablero; tooltips en todos los puntos.
- Resaltado de código por pasos, `r-stack` con fragmentos, callouts, LaTeX, apéndice sin
  numerar, pizarra, menú, perfiles y contenido condicional por perfil.

Paleta: índigo para lo que el sistema decide bien y naranja para la lectura equivocada y su
reparación. Los dos pasos de las marcas están validados para daltonismo y contraste sobre el
papel y sobre la tinta.
