# Estação de Solo — Raspberry Pi (backend de visão e controlo)

> A Raspberry Pi da escola observa o Ornithopter com uma câmara, calcula o seu estado (posição, altitude, rotação) e envia comandos ao ESP32. O drone passa a voar **autónomo** — sem app, sem operador.

## 1. Arquitetura

```
        ┌───────────────────────────── Wi-Fi 2,4 GHz ─────────────────────────────┐
        │                 UDP · protocolo CRTP (Crazyflie)                        │
        ▼                                                                         │
┌──────────────────┐        ┌──────────────────────────────────────────────────┐  │
│  ORNITHOPTER     │        │  RASPBERRY PI 4 (estação de solo)                │  │
│  ESP32 + MPU9250 │◄───────│  · câmara aponta para a zona de voo              │  │
│  firmware        │  setp. │  · OpenCV: deteta o marcador no drone            │  │
│  esp-drone       │        │  · calcula x, y, z (altitude), roll, pitch, yaw  │  │
└──────────────────┘        │  · PID externo → velocidades por motor           │  │
        ▲                   │  · FastAPI: painel de controlo no browser        │  │
        │                   └──────────────────────────────────────────────────┘  │
        └────────────────── telemetria (estado) ─────────────────────────────────┘
```

**Porquê esta divisão?**
- O ESP32 mantém o **PID interno** (estabilização a 500 Hz com o IMU) — exige timing rígido, não deve partilhar com visão.
- A RPi faz o **loop externo** (posição/altitude a ~30 Hz) — é o padrão Crazyflie: *position controller* no chão, *stabilizer* no drone.
- Protocolo: **CRTP over UDP**, o mesmo que o cfclient usa — não inventamos nada.

## 2. Como é que o drone é seguido (a tua pergunta)

O drone leva um **marcador ArUco impresso** (4×4 cm) na parte de baixo/inferior da carenagem:

1. A câmara da RPi captura a ~30–60 fps.
2. OpenCV (dicionário `aruco.DICT_4X4_50`) devolve os 4 cantos do marcador.
3. De cada frame extraímos:
   - **x, y** (posição no plano) → centróide dos cantos, convertido para cm com calibração da câmara.
   - **z (altitude)** → `solvePnP` com o tamanho real do marcador (4 cm conhecidos) — sem sensor extra!
   - **yaw (rotação)** → ângulo do vetor entre cantos do marcador.
   - **roll/pitch estimados** → mudança da forma aparente do quadrilátero (aproximação; o roll/pitch fino continua a vir da telemetria do IMU).
4. Um PID externo compara com o alvo (ex.: pairar a 50 cm sobre um ponto) e gera **setpoints de roll/pitch/thrust/yaw-rate**.
5. Os setpoints vão por UDP ao ESP32, que os mistura nos 4 motores.

**Alternativa ainda mais simples (Plano B):** 2 marcadores de cores (uma em cada braço frontal) → OpenCV `inRange` por cor → mais robusto a distância e luz, sem dependência do módulo `cv2.aruco`.

## 3. Mapa das funções que propuseste → implementação

| Função (a tua ideia) | Onde corre | Como |
|---|---|---|
| **Calcular altitude** | RPi (visão) | `solvePnP` com marcador ArUco de 4 cm conhecidos |
| **Fazer o seguimento dos corpos em tempo real** | RPi (visão) | OpenCV ArUco / cores; IDs diferentes = "corpos" diferentes (multi-drone no futuro) |
| **Gerir o movimento do drone** | RPi (controle) | Máquina de estados: IDLE→TAKEOFF→HOVER→GOTO→LAND + PID externo |
| **Calcular a rotação atual do drone** | RPi (visão) + ESP32 (IMU) | Yaw do marcador por visão; roll/pitch finos por telemetria CRTP do IMU |
| **Calcular a velocidade a usar em cada motor e a direção** | ESP32 (mixer) | Setpoints → PID interno → mistura X: `M1=T−P−R+Y, M2=T+P−R−Y, M3=T+P+R+Y, M4=T−P+R−Y` |

## 4. Endpoints do painel (FastAPI)

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Painel com vídeo + telemetria ao vivo |
| POST | `/takeoff` | Decolagem para altitude alvo (default 50 cm) |
| POST | `/land` | Aterrar |
| POST | `/goto {x,y,z}` | Ir para ponto |
| POST | `/emergency` | Motores OFF imediatamente |
| WS | `/ws/telemetry` | Telemetria em tempo real (x, y, z, r/p/y, bateria) |

## 5. Segurança (autonomia = regras extra)

- Botão físico de **kill** na RPi (GPIO) e comando `/emergency` sempre ativo.
- **Watchdog:** se a RPi perder o marcador > 1 s → `LAND` automático.
- Geofence por software (zona de voo máx. 2×2 m, altura máx. 1,5 m).
- Bateria do drone < 3,4 V → aterragem automática.
- Sempre: voo amarrado nas primeiras sessões.

## 6. Requisitos (tudo grátis, tudo na escola)

```
Raspberry Pi 4 (escola) + câmara CSI/USB (escola)
Python 3.9+ · opencv-python · opencv-contrib-python (aruco) · fastapi · uvicorn · numpy
ESP32 já a correr esp-drone (modo CRTP over UDP já suportado)
```

---

*Referência: arquitetura cfclient/Crazyflie (position controller externo + stabilizer interno) e `espressif/esp-drone`.*
