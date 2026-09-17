# Ornithopter — Estudo de Viabilidade

> Drone estilo **Dune** (thopter), controlado por **ESP32** com firmware open-source **ESP-Drone** (Espressif). Mini brushed, voo estabilizado por app de telemóvel via Wi-Fi. Orçamento máximo: **70 €**.

---

## 1. Decisão de arquitetura

**Porquê um quadcóptero com carenagem estilo Dune (e não um ornitóptero de asas batentes)?**

| Critério | Ornitóptero real (asas batem) | Quadcóptero "thopter" |
|---|---|---|
| Controlo de voo | Muito difícil (ninguém faz estabilização académica disto) | Maduro: firmware Crazyflie/ESP-Drone pronto |
| Risco de não voar | Alto | Baixo |
| Estética Dune | Exata | Adaptada (asas fixas escondem os 4 rotores) |
| Foco do trabalho | Mecânica (ruido, falha) | Eletrónica + software (o que a aula avalia) |

**Veredicto:** quadcóptero X-frame com uma carenagem superior em forma de "thopter" e 4 anéis de proteção estilo motor-gondola de Dune. Voa de verdade e tem a estética.

## 2. Configuração de voo

- **Frame:** X quadrado, 65–80 mm (motor-to-motor), chassi em PLA/PETG impresso 3D ou contraplacado 2 mm.
- **Motores:** 4 × **8520 coreless brushed** (8,5 mm × 20 mm), 3,7 V, ~55 000 rpm, ~15–20 g de empuxo cada a 3,7 V.
- **Hélices:** 65 mm (2 pares CW + CCW), tipo *Gemfan 65mm* — o par CW/CCW é o que permite ao firmware contrariar o *torque* (yaw).
- **Bateria:** **1S LiPo 300–450 mAh** (3,7 V nominal, 4,2 V carregada), com conector JST-PH 2.0.
- **Controlador:** **ESP32-WROOM-32** (fornecido pela escola) — faz de *flight controller* + *radio link* Wi-Fi (2,4 GHz), sem rádio extra.
- **IMU:** **MPU-9250** (giroscópio + acelerómetro + magnetómetro, I2C/SPI) — recomendado pelo schematic do ESP-Drone; alternativas: MPU-6050 (só giro+acc) ou ICM-42688.
- **Driver dos motores:** 4 × MOSFET N-channel em SOT-23 (ex.: **AO3400A**) com resistor de gate 100 Ω e flyback diode, um por motor — é a arquitetura do schematic oficial do ESP-Drone.

## 3. Contas de voo (a parte que interessa provar)

**Peso estimado (AF — all-up weight):**

| Componente | Peso |
|---|---|
| 4 × motor 8520 | ~4 × 5,0 g = 20 g |
| 4 × hélice 65 mm | ~4 × 0,5 g = 2 g |
| Bateria 1S 450 mAh | ~13 g |
| ESP32-WROOM-32 (devkit) | ~10 g |
| MPU-9250 breakout | ~2 g |
| Chassi + carenagem PLA | ~20–25 g |
| Cablagem, MOSFETs, parafusos, LEDs | ~8 g |
| **Total** | **~75–80 g** |

**Empuxo:** 4 motores × ~17 g = **~68 g** a 3,7 V... insuficiente para um AF de 80 g.
- A 4,0–4,2 V (bateria cheia) o empuxo sobe para ~22 g/motor → **~88 g**.
- **Regra de ouro:** empuxo ≥ 2× peso. Para AF = 80 g queremos **~160 g de empuxo**.
- **Solução:** usar a variante **820 coreless (55 000 rpm, ~25 g empuxo)** ou motores 8520 "high thrust" (~24 g), ou reduzir o AF para <45 g com chassi minimalista (estilo Crazyflie: ~27 g).

**Alvo final:** AF ≈ 70 g, empuxo ≈ 140–160 g → razão empuxo/peso **2,0–2,3** ✔ (hover a ~45–50 % de throttle, sobra para manobrar).

**Corrente:** 4 motores × ~0,6 A em hover ≈ **2,4 A**; pico ~5 A. Uma 1S 450 mAh a 25C entrega 11 A — folga ✔.
**Autonomia:** 450 mAh / 2,4 A ≈ **11 min em hover** (realista: 6–8 min com manobras).
**Potência:** 3,7 V × 2,4 A ≈ **9 W em hover**, ~18 W pico.

## 4. Estabilidade (o que o firmware faz)

- **Loop de controlo a 500 Hz:** PID em cascata (rate → attitude), igual ao Crazyflie. O MPU-9250 mede rotações a 1 kHz.
- **Modos:** *Stabilize* (ângulos limitados, sempre estável), *Height-hold* (com barómetro BMP280 opcional, +2 €) e *Position-hold* (com fluxo ótico PMW3901, +12 € — opcional, fica fora do orçamento base).
- **Mistura X:** firmware mistura throttle + roll + pitch + yaw nos 4 motores (M1..M4), CW/CCW alternados.

## 5. Ligações (esquema elétrico resumido)

```
Bateria 1S ──┬── VCC 3,7V ──┬─────────────┬──────────────┐
             │              │             │              │
           (SW)          MOSFET M1..M4 (AO3400A)    VIN ESP32
             │              │             │              │
             └── GND ───────┴── GND ──────┴──────────────┘
                            ▲
              Gate de cada MOSFET ◄── GPIO 4/12/13/14 (ESP32) via 100Ω
              MPU-9250: SDA→GPIO21, SCL→GPIO22 (I2C, 3V3 + GND)
```

- Motores: + do motor ao + da bateria; − do motor ao **drain** do MOSFET; **source** ao GND.
- ESP32 alimenta-se pela bateria via pino **VIN/5V** (regulador onboard aguenta 4,2 V — confirmar devkit).
- LEDs indicadores em GPIO 2 (e ring WS2812 opcional para efeito "spice" laranja de Dune).

## 6. Software (o que já existe, não inventamos)

- **Firmware:** `espressif/esp-drone` (GitHub) — GPL3.0, portado do Crazyflie. Suporta ESP32/ESP32-S2/S3, IDF v5.0.
- **App:** `ESP-Drone-iOS` / `ESP-Drone-Android` (open-source) — liga por Wi-Fi ao drone e controla.
- **O que fazemos:** configurar GPIOs no `menuconfig` para os nossos pinos, calibrar IMU, ajustar PID.

## 7. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Empuxo insuficiente | Motores "high thrust" ou chassi < 50 g; testar empuxo antes de montar |
| Peso da carenagem | Carenagem em PLA fino (0,8 mm) ou cartão plástico; ≤ 25 g |
| IMU barata descalibrada | Calibração do firmware + montagem firme com espuma dupla-face |
| Interferência Wi-Fi no IMU | Afastar MPU-9250 do ESP32 ≥ 2 cm; fios torcidos |
| Soldadura de MOSFET SOT-23 | Usar adaptador SOT-23→DIP ou MOSFET TO-92 (mais fácil de soldar) |

---

*Fonte: repositório `espressif/esp-drone` (GitHub), especificações típicas de motores coreless 8520/820 de fabricantes (estimativas), cálculos próprios.*
