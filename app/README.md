# 📱 Ornithopter App (Expo)

App de controlo do drone Ornithopter em **Expo/React Native** — corre em Android/iOS via Expo Go, sem compilar nada.

## Arquitetura de comando

```
TELEMÓVEL (app Expo)      RASPBERRY PI (FastAPI)         ESP32 (esp-drone)
┌──────────────────┐     ┌──────────────────────┐      ┌───────────────┐
│ botões + telem.  │────►│ POST /takeoff /land  │────► │ mixer → 4     │
│ telemetria live  │◄────│ WS   /ws/telemetry   │◄──── │ motores + IMU │
└──────────────────┘HTTP └──────────────────────┘ UDP  └───────────────┘
```

- A app **nunca** fala com o drone diretamente — só com a estação de solo (RPi). É ela que aplica as regras de segurança (watchdog, geofence, bateria) a *qualquer* comando, venha ele da app, do painel web ou de um script.
- Telemetria em tempo real por WebSocket (`/ws/telemetry`): modo, posição x/y/z, atitude, bateria, estado do marcador.

## Ecrãs

1. **Ligação** — IP da estação de solo (rede da escola)
2. **Painel** — telemetria live + DECOLAR / ATERRAR
3. **EMERGENCY** — botão sempre visível, motores OFF imediato
4. *(próximo)* **Joystick virtual** — 2 pans → `/goto x,y`

## Correr

```bash
cd app
npm install
npx expo start        # abre no telemóvel com Expo Go (mesma rede Wi-Fi da RPi)
```

## Integração com a estação de solo

A app consome exatamente os endpoints já definidos em [`docs/ground-station.md`](../docs/ground-station.md):

| App | Endpoint RPi |
|---|---|
| LIGAR | `GET /` (painel) + `WS /ws/telemetry` |
| DECOLAR | `POST /takeoff` |
| ATERRAR | `POST /land` |
| Ir para (x,y) | `POST /goto?x=&y=` |
| EMERGENCY | `POST /emergency` |

## Estado

- [x] Esqueleto Expo (ligação, telemetria, comandos de voo)
- [ ] Joystick virtual (gestos → /goto)
- [ ] Modo FPV (stream MJPEG da câmara da RPi) — **extra**
- [ ] Config persistente do IP (AsyncStorage)
