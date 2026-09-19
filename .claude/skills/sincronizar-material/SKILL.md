---
name: sincronizar-material
description: Sincroniza el material del curso desde el Aula Virtual UPC a materials/ usando el comando `aula` de chrome-helper. Úsala cuando falte material, el profesor publique algo nuevo, se vayan a consultar notas o retroalimentación, o al empezar en una máquina donde materials/ está vacío (es carpeta no versionada). También para descubrir documentos nuevos y actualizar manifest.json.
---

# Sincronizar material del Aula Virtual

`materials/` **no está versionado** (el repo es público y son slides, enunciados y
rúbricas del profesor). En una máquina nueva la carpeta está vacía y hay que
reconstruirla. `manifest.json` sí se versiona y es la receta completa.

La herramienta es `aula`, del repo `~/Code/personal/chrome-helper`, instalada
global con `uv tool install --editable .`.

## Procedimiento

Siempre desde la raíz del repo del curso; `aula` opera sobre el directorio actual.

```bash
aula check      # ¿sigue viva la sesión?
aula discover   # recorre el curso y añade al manifiesto lo nuevo
aula sync       # baja a materials/ lo que falte
aula status     # cuántos adjuntos hay y cuántos faltan
```

Si `aula check` dice que la sesión caducó:

```bash
aula login      # abre Chrome; el usuario se autentica a mano (MFA incluido)
```

**`aula login` es interactivo y lo tiene que hacer la persona, no el agente.**
Sugiérele que escriba `! aula login` en el prompt para que la salida caiga en la
conversación. Nunca intentes automatizar el MFA ni pedir credenciales.

Para ver notas, estado de entrega y retroalimentación del docente:

```bash
aula notas
```

## Después de sincronizar

- Si `discover` cambió `manifest.json`, **commitea el manifiesto** (es la receta;
  sin él no se puede reconstruir nada). Los archivos de `materials/` no: están
  en `.gitignore`.
- Si aparecen documentos nuevos, merece la pena actualizar
  `materials/AULA-VIRTUAL-ESTADO.md`, que sí se versiona.
- Si el material nuevo es un enunciado de trabajo, dilo explícitamente: puede
  cambiar las prioridades del ciclo.

## Lo que ya costó caro

- **La sesión de Blackboard no persiste en disco.** Lo que sobrevive es la cookie
  del SSO de Microsoft; `aula` reacuña la sesión sola pasando por el endpoint
  SAML. Por eso `check` puede decir "activa" aunque haga días de la última vez.
- **El manifiesto no guarda hash por adjunto.** Si el profesor reemplaza un
  archivo manteniendo el nombre, `sync` no se entera y se queda con el viejo.
  Ante la duda con un archivo concreto, bórralo y vuelve a sincronizar.
- **`schema_version`**: el manifiesto de agosto era v1 y no traía URL por
  adjunto, solo el estado `blocked_by_browser_policy`. `discover` lo migra a v2,
  que sí las trae. Si ves entradas sin `url`, corre `discover` antes que `sync`.
- **Entradas duplicadas**: si un documento se republica con otro título, el
  merge puede dejar el mismo adjunto en dos entradas, una sin `url`, y `sync`
  falla con `KeyError: 'url'`. El archivo suele bajar igual por la entrada
  buena; la huérfana hay que limpiarla a mano.
