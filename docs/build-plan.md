# Ornithopter — Plano de Construção (componente a componente)

> Filosofia da aula: **nada de kits perfeitos** — cada bloco é construído, testado e compreendido individualmente antes do seguinte.

## Bloco 0 — Antes de comprar (1 aula)

1. Imprimir `cad/ornithopter.scad` → exportar `frame_flat()` em STL → confirmar com o professor a impressão 3D.
2. Encomendar BOM (`docs/bom.md`) — AliExpress demora 2–4 semanas.
3. Instalar ESP-IDF v5.0 e clonar `espressif/esp-drone` (teste de compilação com placa vazia).

## Bloco 1 — Bancada de motores (sem voar)

1. Soldar 1 motor a 1 MOSFET numa protoboard com resistor de gate.
2. Acionar com um GPIO do ESP32 (sinal PWM 500 Hz do LEDC).
3. Medir corrente e empuxo numa balança de cozinha (motores apontando para baixo).
4. **Critério de passe:** ~20 g de empuxo por motor a 3,7 V.

## Bloco 2 — IMU e estimativa de atitude

1. Ligar MPU-9250 por I2C e ler registos brutos com exemplo do ESP-IDF.
2. Verificar que roll/pitch respondem corretamente ao inclinar a placa à mão.
3. Calibrar gyro (comando do firmware) com a placa imóvel.
4. **Critério de passe:** leitura estável ±2° com a placa parada.

## Bloco 3 — Firmware de voo

1. Configurar `menuconfig`: pinos dos motores, I2C, IMU.
2. Flash e ligar pela app ESP-Drone (Wi-Fi "ESPDRONE-xxxx").
3. Teste no chão: arm/disarm, resposta dos 4 motores aos comandos.
4. **Critério de passe:** os 4 motores respondem ao joystick, sem vibrar.

## Bloco 4 — Montagem completa

1. Montar motores no frame, cablar, fixar bateria com velcro.
2. Centro de gravidade no centro do frame X (deslizar a bateria até equilibrar).
3. Teste de voo amarrado (fio de pesca num mastro) — ajustar PIDs.
4. **Critério de passe:** hover estável > 10 s amarrado.

## Bloco 5 — Carenagem estilo Dune (só depois de voar!)

1. Imprimir/levar a carenagem leve (≤ 25 g).
2. Re-testar voo amarrado com carenagem.
3. Demonstração final: decolagem, hover, aterragem controlada.

## Checklist de segurança

- [ ] Hélices FORA em todos os testes elétricos
- [ ] Óculos de proteção ao testar hélices postas
- [ ] Bateria LiPo guardada em saco à prova de fogo, nunca abaixo de 3,3 V
- [ ] Nunca arm/disarm com hélices à frente de pessoas
- [ ] Carregar LiPo sempre supervisionado
