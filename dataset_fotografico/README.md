# Dataset fotográfico

Fotos reales de tableros KenKen tomadas con un celular, para medir lo que los PDF de KrazyDad
no tienen: sombras, perspectiva, curvatura del papel, desenfoque. Las fotos no se versionan en
el repo; viven en dos lugares:

- **Hugging Face:** [rosewt/kenken-tb1-fotos](https://huggingface.co/datasets/rosewt/kenken-tb1-fotos),
  en `fotos_reales/`, junto con 12 tableros sintéticos de muestra en `sinteticos/`.
- **Release [`tb1`](https://github.com/R0SEWT/cs-topics/releases/tag/tb1):** las mismas fotos,
  en `TB1-KenKen-fotos.zip`.

Son 8 tomas (`foto01.jpg` a `foto08.jpg`) hechas con un Pixel 9a el 8 de octubre de 2026, a
distintas distancias, ángulos e iluminación, de un mismo tablero: el 6×6 sintético de la Fig. 2
del informe, mostrado en una pantalla. Cada `.json` es la respuesta del nodo para esa foto. La de
la portada es `foto04.jpg`; `presentacion/datos/img/f1_foto.jpg` es su copia en grises, reducida
a 1200 px de alto.

Para trabajar con ellas en local, descomprímelas en `dataset_fotografico/fotos/` (está en el
`.gitignore`).

## Lo que falta

La primera versión de este archivo citaba la rúbrica: al menos 10 fotos en condiciones
variadas, incluidas versiones impresas. Las 8 de ahora son de un solo tablero en una pantalla;
faltan fotos de tableros impresos.

## Sumar fotos

El nodo puede archivar cada foto que recibe, junto con lo que respondió, mientras se usa la app
con tableros impresos:

```bash
cd labs/tb1-kenken
uv run python -m kenken_nodo --guardar ../../dataset_fotografico/fotos
```

Conviene variar las condiciones: luz de día, sombra y flash; rotación leve; papel curvado.
