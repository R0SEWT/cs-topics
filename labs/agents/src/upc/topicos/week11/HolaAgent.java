package upc.topicos.week11;

import jade.core.Agent;
import jade.core.behaviours.OneShotBehaviour;

/** Agente mínimo: comprueba que la plataforma JADE arranca y ejecuta un behaviour. */
public class HolaAgent extends Agent {

    @Override
    protected void setup() {
        addBehaviour(new OneShotBehaviour() {
            @Override
            public void action() {
                System.out.println("[" + getAgent().getLocalName() + "] agente activo en JADE");
                getAgent().doDelete();
            }
        });
    }
}
