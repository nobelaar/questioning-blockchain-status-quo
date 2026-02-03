# Análisis de Poder en Linea (L2 de Ethereum)

Este proyecto analiza la **distribución real del poder operativo** en la red Linea (Layer 2 de Ethereum),
utilizando técnicas básicas de Data Science aplicadas a datos on-chain.

El foco no está en la narrativa de descentralización, sino en la **estructura efectiva de control**
sobre la producción de bloques y el ordering de transacciones.

---

## 🎯 Objetivo

Investigar quién ejerce el poder real en Linea a través del análisis de:

- Producción de bloques
- Concentración de control
- Resiliencia operativa del sistema
- Potencial de censura y control del ordering

---

## 🧠 Hipótesis Iniciales

1. **Distribución del poder**  
   La producción de bloques está concentrada en pocos actores.

2. **Influencia vs visibilidad**  
   Actores con baja visibilidad pública pueden ejercer alto control operativo.

3. **Resiliencia**  
   El sistema depende críticamente de un conjunto reducido de operadores.

4. **Centralización encubierta**  
   Un pequeño subconjunto de nodos puede afectar el consenso o censurar transacciones.

---

## 📦 Dataset

Los datos se obtienen directamente desde el RPC público de Linea:

- `block_number`
- `timestamp`
- `proposer` (address que produce el bloque)

Fuente:
- RPC público de Linea (`https://rpc.linea.build`)

---

## 🛠️ Stack Técnico

- Python
- web3.py
- pandas
- matplotlib

No se utiliza Machine Learning en esta etapa.  
El objetivo es **comprender la estructura del sistema**, no predecirla.

---

## 🔍 Resultados – Fase 1 (Producción de Bloques)

- En el rango analizado, **el 100% de los bloques fueron producidos por una única address**.
- La producción de bloques en Linea está completamente centralizada.
- El control del ordering de transacciones depende de un solo operador.

### Implicaciones

- Poder absoluto de censura a nivel operativo.
- Resiliencia nula frente a fallas o presión externa sobre el operador.
- La descentralización de Linea (si existe) **no se encuentra en la capa de block production**.

---

## 📌 Conclusión

Este análisis muestra que, al menos en la capa de producción de bloques,
Linea opera actualmente como un sistema **centralizado**.

La descentralización no debe evaluarse únicamente por el discurso o el diseño teórico,
sino por **quién controla efectivamente la ejecución del sistema**.

---

## 🚧 Próximos Pasos

- Análisis temporal del proposer (cambios históricos).
- Estudio de patrones de ordering y posible MEV.
- Comparación con otras L2 (Optimism, Arbitrum, Base).
- Profundización en capas no visibles desde block production.

---

## 📎 Nota

Este proyecto tiene fines exploratorios y educativos.
Los resultados reflejan el estado observado en el rango de bloques analizado.
