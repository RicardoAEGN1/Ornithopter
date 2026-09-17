# Estação de Solo — Raspberry Pi (backend de controlo)

> A Raspberry Pi da escola recebe comandos da **app Expo (telemóvel)** e do painel web, aplica as regras de segurança e envia setpoints ao ESP32. A **câmara** é um **extra opcional** de demonstração (seguimento autónomo por ArUco) — o drone voa e é comandável mesmo sem ela.

## 1. Modos de operação

| Modo | Câmara | Seguimento | Quem comanda |
|---|---|---|---|
| **A — Manual (base)** | ❌ | ❌ | App Expo / painel web → RPi → drone |
| **B — Autónomo (extra)** | ✔ | ✔ ArUco | Mission planner da RPi (demo de capacidade) |

No modo A, a altitude e a estabilização ficam a cargo do firmware (height-hold com barómetro BMP280 opcional) e dos comandos diretos da app. O modo B demonstra coordenação por visão — é o *show-off* científico, não o requisito.

## 2. Arquitetura

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

## 3. Como é que o drone é seguido (extra opcional)

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

## 3. Controlo por app Expo (telemóvel)

O telemóvel fala **sempre com a RPi** (nunca com o drone):

```
app Expo ──HTTP POST /takeoff /land /goto /emergency──► RPi ──UDP──► ESP32
app Expo ◄──WebSocket /ws/telemetry (10 Hz)──────────── RPi ◄─────── ESP32
```

- **Porquê passar sempre pela RPi?** Ponto único de segurança: a RPi valida geofence, bateria e watchdog **antes** de retransmitir qualquer comando — venha ele da app, do painel web ou do planner autónomo.
- A app (pasta `app/`) tem: ecrã de ligação por IP, telemetria live, DECOLAR/ATERRAR e botão EMERGENCY sempre visível.
- *Extra:* stream MJPEG da câmara no ecrã da app (FPV pela RPi) — só útil no modo B.

## 4. Mapa das funções que propuseste → implementação

| Função (a tua ideia) | Onde corre | Como |
|---|---|---|
| **Calcular altitude** | RPi (visão) | `solvePnP` com marcador ArUco de 4 cm conhecidos |
| **Fazer o seguimento dos corpos em tempo real** | RPi (visão) | OpenCV ArUco / cores; IDs diferentes = "corpos" diferentes (multi-drone no futuro) |
| **Gerir o movimento do drone** | RPi (controle) | Máquina de estados: IDLE→TAKEOFF→HOVER→GOTO→LAND + PID externo |
| **Calcular a rotação atual do drone** | RPi (visão) + ESP32 (IMU) | Yaw do marcador por visão; roll/pitch finos por telemetria CRTP do IMU |
| **Calcular a velocidade a usar em cada motor e a direção** | ESP32 (mixer) | Setpoints → PID interno → mistura X: `M1=T−P−R+Y, M2=T+P−R−Y, M3=T+P+R+Y, M4=T−P+R−Y` |

## 6. Endpoints do painel e da app (FastAPI)

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Painel com vídeo + telemetria ao vivo |
| POST | `/takeoff` | Decolagem para altitude alvo (default 50 cm) |
| POST | `/land` | Aterrar |
| POST | `/goto {x,y,z}` | Ir para ponto |
| POST | `/emergency` | Motores OFF imediatamente |
| WS | `/ws/telemetry` | Telemetria em tempo real (x, y, z, r/p/y, bateria) |

## 7. Segurança

- Botão físico de **kill** na RPi (GPIO) e comando `/emergency` sempre ativo.
- **Watchdog:** se a RPi perder o marcador > 1 s → `LAND` automático.
- Geofence por software (zona de voo máx. 2×2 m, altura máx. 1,5 m).
- Bateria do drone < 3,4 V → aterragem automática.
- Sempre: voo amarrado nas primeiras sessões.

## 8. Requisitos (tudo grátis, tudo na escola)

```
Raspberry Pi 4 (escola) + câmara CSI/USB (escola)
Python 3.9+ · opencv-python · opencv-contrib-python (aruco) · fastapi · uvicorn · numpy
ESP32 já a correr esp-drone (modo CRTP over UDP já suportado)
```

---

*Referência: arquitetura cfclient/Crazyflie (position controller externo + stabilizer interno) e `espressif/esp-drone`.*
