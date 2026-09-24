# JADE / FIPA — Unidad 5. Sin Maven ni Gradle: javac + lib/*.jar.
JAVAC   := javac
JAVA    := java
SRC_DIR := src
OUT_DIR := build
# "=" y no ":=": los jars los baja `deps`, así que el classpath se arma al
# ejecutar la receta, no al leer el Makefile (en un clon limpio aún no están).
CP       = $(OUT_DIR):$(shell ls lib/*.jar 2>/dev/null | tr '\n' ':')
SOURCES := $(shell find $(SRC_DIR) -name '*.java')

# Agente a lanzar: make run AGENT=upc.topicos.week11.HolaAgent
AGENT ?= upc.topicos.week11.HolaAgent
NAME  ?= a1

.PHONY: all deps build run gui clean

all: build

deps:                ## Baja jade.jar y commons-codec desde Maven Central
	./fetch-deps.sh

build: deps          ## Compila todo src/ a build/
	@mkdir -p $(OUT_DIR)
	$(JAVAC) -d $(OUT_DIR) -cp "$(CP)" $(SOURCES)

run: build           ## Arranca la plataforma con un agente: make run AGENT=... NAME=...
	$(JAVA) -cp "$(CP)" jade.Boot -gui -agents "$(NAME):$(AGENT)"

nogui: build         ## Igual que run pero sin la GUI de administración
	$(JAVA) -cp "$(CP)" jade.Boot -agents "$(NAME):$(AGENT)"

clean:
	rm -rf $(OUT_DIR)
