# 🚁 ORNITHOPTER

> Drone quadcóptero estilo **Dune** (thopter), controlado por **ESP32** com firmware open-source **ESP-Drone** (Espressif). Projeto escolar de eletrónica — construído componente a componente, sem kits.

## Números-chave

| Métrica | Valor |
|---|---|
| Peso total (AF) | ~78 g |
| Empuxo | ~150 g (razão 2,0×) |
| Autonomia | 6–11 min |
| Custo total | **44,30 €** (orçamento 70 €) |
| Loop de controlo | PID 500 Hz |
| Controlo | App iOS/Android via Wi-Fi 2,4 GHz |

## Estrutura

```
docs/           Viabilidade, BOM (lista de materiais), pinout, plano de construção
cad/            Modelo paramétrico OpenSCAD (frame + carenagem estilo Dune)
presentation/   Apresentação HTML do projeto (abrir no browser)
```

## Documentos

- [`docs/viability.md`](docs/viability.md) — estudo de viabilidade (arquitetura, empuxo/peso, potência, estabilidade)
- [`docs/bom.md`](docs/bom.md) — lista de materiais com fornecedores e custos
- [`docs/wiring.md`](docs/wiring.md) — pinout ESP32 e esquema de ligações
- [`docs/build-plan.md`](docs/build-plan.md) — plano de construção em blocos com critérios de passe
- [`cad/ornithopter.scad`](cad/ornithopter.scad) — CAD paramétrico (OpenSCAD → STL)
- [`presentation/ornithopter.html`](presentation/ornithopter.html) — apresentação do projeto

## Stack

| Camada | Tecnologia |
|---|---|
| Flight controller | ESP32-WROOM-32 (escola) |
| Firmware | [espressif/esp-drone](https://github.com/espressif/esp-drone) (ESP-IDF v5.0, GPL-3.0) |
| IMU | MPU-9250 (I2C) |
| Motores | 4× coreless 8520 + MOSFET AO3400A |
| Bateria | LiPo 1S 450 mAh 25C |
| App | [ESP-Drone-Android](https://github.com/EspressifApps/esp-drone-android) / iOS |
| CAD | OpenSCAD |

*"The spice must flow."* 🕌
