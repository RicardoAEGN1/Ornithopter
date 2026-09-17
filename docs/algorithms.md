# Sistemas e Algoritmos — Coordenação, Navegação e Controlo

> Documento teórico do Ornithopter: como as partes se coordenam (RPi ↔ ESP32 ↔ motores) e que algoritmos fazem o drone pairar, navegar e aterrar. Sem código — só conceitos, diagramas e matemática.

## 1. Visão global: três camadas de controlo

```
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 3 — MISSION PLANNER (RPi, ~1 Hz)                     │
│  máquina de estados: IDLE → TAKEOFF → HOVER → GOTO → LAND    │
│  decide O QUÊ fazer (pontos de passagem, geofence, segurança)│
├──────────────────────────────────────────────────────────────┤
│  CAMADA 2 — POSITION CONTROLLER (RPi, ~30 Hz)                │
│  PID externo: posição (x,y,z) → setpoints de atitude         │
│  decide COMO se mover (roll/pitch/thrust desejados)          │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 1 — STABILIZER (ESP32, 500 Hz)                       │
│  PID interno: atitude desejada → velocidades dos 4 motores   │
│  (mixer X) usando o giroscópio/accelerómetro do MPU-9250     │
└──────────────────────────────────────────────────────────────┘
```

Esta divisão é o padrão da indústria (Crazyflie, PX4, ArduPilot): **quanto mais rápido o loop, mais perto do hardware**. O ESP32 não sabe "para onde ir" — só sabe manter a atitude que lhe mandam; a RPi não toca nos motores — só manda intenções.

## 2. Estimador de atitude (ESP32): filtro complementar

O giroscópio é rápido mas deriva; o acelerómetro é estável mas ruidoso. O **filtro complementar** junta os dois:

```
ângulo = α · (ângulo + gyro · dt) + (1 − α) · atan2(acc_y, acc_z)

α ≈ 0,98  →  confia 98 % no gyro entre medições,
             corrige 2 % com o acelerómetro (que conhece "para baixo")
```

- Frequência de corte: `α = τ/(τ+dt)`, com τ ≈ 0,5 s.
- O yaw não pode ser corrigido pelo acelerómetro (a gravidade não gira no plano horizontal) → usa-se o **magnetómetro** do MPU-9250, ou aceita-se deriva lenta de yaw (ok para demo indoor).

## 3. PID em cascata (ESP32): o coração da estabilização

Dois PIDs encadeados por eixo (roll, pitch, yaw-rate):

```
setpoint atitude (graus)          ← vem da RPi
        │
        ▼
  ┌─────────┐  erro de ângulo   ┌─────────┐  velocidade
  │ PID     │ ────────────────►  │ PID     │ ───────────►  mistura
  │ ANGULAR │   (graus)          │ RATE    │               X (M1..M4)
  └─────────┘                    └─────────┘                    │
        ▲                             ▲                        ▼
   ângulo estimado               gyro (rad/s)          PWM 20 kHz nos MOSFETs
   (filtro compl.)               a 1 kHz
```

**Porquê cascata?** O loop interno (rate) é 10× mais rápido e amortece perturbações (rajadas, vibração) antes de chegarem ao ângulo — o mesmo princípio de um piloto automático real.

**Sintonia (Ziegler–Nichols na bancada):**
1. Ki = Kd = 0; subir Kp até oscilar → Kp_final = 0,6·Kp_osc
2. Kd ≈ 0,1·Kp (amortecer); Ki pequeno (corrigir deriva de hover)
3. Valores de partida típicos para mini-quads: rate Kp≈0,25 · angular Kp≈4,5

## 4. Mistura X (mixer): setpoints → 4 motores

```
M1 (CCW) = T − P − R + Y      M2 (CW)  = T + P − R − Y
M4 (CW)  = T − P + R − Y      M3 (CCW) = T + P + R + Y

T = thrust  P = pitch  R = roll  Y = yaw-rate
```

| Movimento | O que muda |
|---|---|
| Subir | T igual nos 4 |
| Pitch (frente/trás) | diferença frente ↔ trás |
| Roll (esq/dir) | diferença esquerda ↔ direita |
| Yaw (rodar) | pares CW vs CCW (torque reação) |

Cada Mi é normalizado a [0..1] antes do PWM. Se algum ultrapassa 1 (saturação), reduz-se T igualmente nos 4 — mantém a atitude em vez do empuxo (regra de segurança).

## 5. Algoritmos de coordenação RPi ↔ drone

### 5.1 Seguimento visual (ArUco)

1. Detetar cantos do marcador (dicionário 4×4) a 30 fps.
2. `solvePnP`: com 4 cantos + tamanho real (40 mm) → rotação e translação da câmara → **x, y, z do drone**.
3. Suavizar com **filtro de Kalman 1D** por eixo (prevê entre frames; rejeita outliers de deteção falhada).
4. Se perdido > 1 s → trigger de segurança (LAND).

### 5.2 Controlo de posição (PID externo na RPi)

```
erro_x = x_alvo − x_drone  →  pitch_cmd = Kp·erro_x + Ki·∫erro + Kd·(derivada)
erro_z = z_alvo − z_drone  →  thrust_cmd = hover_thrust + PID_z(erro_z)
```

- **Estratégia antiderivada (derivative kick):** derivar a medição, não o erro — evita saltos quando o alvo muda.
- **Integral limitado (anti-windup):** clampa ∫ para não acumular enquanto o drone arranca.

### 5.3 Máquina de estados (mission planner)

```
        takeoff()            z ≥ 95% alvo          goto(x,y)
IDLE ───────────► TAKEOFF ────────────────► HOVER ◄────► GOTO
  ▲                  │                        │             │
  │ land()/auto      │ perdeu marcador        │             │ chegou (<40mm)
  ▼                  ▼                        ▼             ▼
LAND ◄──────── bateria<3.4V ◄── watchdog ── (qualquer estado)
  │
  ▼ z≈0 → motores OFF → IDLE
```

Transições de emergência (watchdog, geofence, bateria) têm **prioridade absoluta** sobre comandos do utilizador.

### 5.4 Coordenação multi-"corpos" (extensão futura)

O dicionário ArUco 4×4 tem 50 IDs → cada drone pode ter um ID. A RPi faz **seguimento simultâneo** e um **alocador de alvos** evita colisões:
- **Caixas de exclusão:** cada drone tem um cilindro de 50 cm; o planner rejeita alvos dentro do cilindro de outro.
- **Prioridade fixa por ID** (determinístico, fácil de explicar na defesa).
- **Alternativa elegante:** algoritmo *repulsion* — cada drone recebe um empurrão virtual proporcional à proximidade do outro (campo potencial artificial).

## 6. Segurança por camadas (defesa em profundidade)

| Camada | Mecanismo | Atuação |
|---|---|---|
| 1 — Hardware | pull-down nos gates | motores OFF se ESP32 reinicia |
| 2 — Firmware | failsafe RC/Wi-Fi | perdeu ligação → motores OFF |
| 3 — Software RPi | watchdog do marcador | LAND automático |
| 4 — Mission | geofence + bateria | rejeita alvos fora; LAND < 3,4 V |
| 5 — Humano | botão EMERGENCY / kill | motores OFF imediato |

## 7. O que medir na bancada (para provar na defesa)

- Latência RPi→ESP32 (setpoint): alvo < 50 ms (Wi-Fi local)
- Latência de loop de visão: alvo < 33 ms/frame (30 fps)
- Erro estático de hover: alvo < ±10 cm (x,y) e < ±5 cm (z)
- Overshoot no degrau de setpoint: alvo < 20 % da altura degrau

---

*Referências: filtro complementar (Kalman/colibry), PID cascata do Crazyflie (`bitcraze/crazyflie-firmware`), ArUco (S. Garrido-Jurado, 2014), mistura X do esp-drone.*
