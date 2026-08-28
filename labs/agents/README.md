# Lab — Agentes JADE / FIPA (Unidad 5)

Stack: **Java 21 + JADE 4.3**, compilado con `javac`. Sin Maven ni Gradle: el curso
reparte los jars a mano y cada sesión son unos pocos `.java`, así que un `Makefile`
sobra para el trabajo.

```bash
cd labs/agents
make deps                                  # baja jade.jar + commons-codec de Maven Central
make build                                 # compila src/ -> build/
make run   AGENT=upc.topicos.week11.HolaAgent NAME=a1   # con GUI de administración
make nogui AGENT=upc.topicos.week11.HolaAgent           # sin GUI
make clean
```

La plataforma **no termina sola**: `jade.Boot` deja el contenedor principal vivo
esperando agentes. Se corta con `Ctrl-C`.

## De dónde salen los jars

Aula Virtual bloqueó la descarga de `jade.jar` y `commons-codec-1.3.jar`
(`manifest.json`, estado `blocked_by_browser_policy`). `fetch-deps.sh` los toma de
Maven Central: `net.sf.ingenias:jade:4.3`, que es el JADE de TILAB reempaquetado
(`jade.Boot`, `jade.core.Agent`, clases FIPA). Verificado arrancando en Java 21.

Los jars están gitignorados — son dependencias reproducibles, no material del curso.
Si el profe entrega una versión distinta, déjala caer en `lib/` y `make deps` la respeta.

## Organización

`src/upc/topicos/weekNN/` — un paquete por sesión (week11 MDP, week12 multiagente,
week13 FIPA), que es como el profe entrega los `.java`.
