# Ornithopter — Ligações ESP32 (pinout e esquema)

> Firmware: `espressif/esp-drone` (ESP-IDF v5.0). Pinos configuráveis no `menuconfig`.

![Diagrama de ligações completo](../assets/wiring-diagram.svg)

## 1. Tabela de ligações

| Sinal | Pino ESP32 | Destino | Notas |
|---|---|---|---|
| Motor M1 (frente-direita, CCW) | GPIO 4 | Gate MOSFET 1 via 100 Ω | LEDC ch0 |
| Motor M2 (trás-direita, CW) | GPIO 12 | Gate MOSFET 2 via 100 Ω | LEDC ch1 |
| Motor M3 (trás-esquerda, CCW) | GPIO 13 | Gate MOSFET 3 via 100 Ω | LEDC ch2 |
| Motor M4 (frente-esquerda, CW) | GPIO 14 | Gate MOSFET 4 via 100 Ω | LEDC ch3 |
| IMU SDA | GPIO 21 | MPU-9250 SDA (I2C) | pull-up 4,7 kΩ a 3V3 |
| IMU SCL | GPIO 22 | MPU-9250 SCL (I2C) | pull-up 4,7 kΩ a 3V3 |
| IMU IRQ | GPIO 36 (input) | MPU-9250 INT | leitura síncrona |
| LED status | GPIO 2 | LED + 220 Ω → GND | onboard do devkit |
| VIN | 5V/VIN | + da bateria (via JST) | regulador onboard |
| GND | GND | − da bateria, sources MOSFETs | comum |

## 2. Cada motor (×4)

```
Bateria (+) ──────────────► fio vermelho do motor
GPIO ──[100 Ω]── Gate AO3400A
                 Drain ◄──── fio azul/branco do motor
                 Source ───► GND
                 (1N4148 entre Drain e +Bateria, catodo ao +)
10 kΩ entre Gate e GND (mantém motor parado se o ESP32 arranca a meio)
```

## 3. MPU-9250

```
ESP32 3V3 ──► VCC  |  GPIO21 ──► SDA  |  GPIO22 ──► SCL  |  GND ──► GND
Montar a ≥ 2 cm do ESP32, com fita dupla-face (isola vibrações)
```

## 4. Checklist de segurança antes de ligar

- [ ] Continuidade GND comum (multímetro)
- [ ] Sem curto +/− da bateria (medição com multímetro, antes do JST)
- [ ] MOSFET no sentido certo (Source ao GND!)
- [ ] Motores giram na direção certa (testar com app, hélices FORA)
- [ ] Primeiro voo amarrado com fio de pesca ao teto/mastro
