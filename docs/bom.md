# Ornithopter — Lista de Materiais (BOM)

> Orçamento máximo: **70 €**. A escola fornece: **ESP32 devkit, ferro de soldar + estanho, cabos, multímetro** (valor evitado: ~15 €).

## 1. Componentes comprados

| # | Componente | Especificação | Fornecedor | Qtd | Preço un. | Subtotal |
|---|---|---|---|---|---|---|
| 1 | Motores coreless 8520 "high thrust" | 8,5×20 mm, 3,7 V, ~24 g empuxo (2× CW + 2× CCW) | AliExpress / Amazon.es | 4 | 2,50 € | **10,00 €** |
| 2 | Hélices 65 mm (2 CW + 2 CCW) | Gemfan 65 mm ou equivalentes | AliExpress / Amazon.es | 4 (+4 reserva) | 0,40 € | **3,20 €** |
| 3 | Bateria LiPo 1S 450 mAh 25C | Com JST-PH 2.0 e protetor | AliExpress / loja RC local | 1 | 7,50 € | **7,50 €** |
| 4 | Carregador 1S USB (micro/USB-C) | Balanceador simples 1S | AliExpress / loja RC local | 1 | 6,00 € | **6,00 €** |
| 5 | IMU MPU-9250 (GY-9250 breakout) | Giro + acel + mag, I2C/SPI | AliExpress / Amazon.es | 1 | 4,50 € | **4,50 €** |
| 6 | MOSFET AO3400A (ou TO-92 equivalente) | N-channel, gate 2,5–4 V | AliExpress (lote 50 pcs) | 4 | 0,10 € | **0,40 €** |
| 7 | Resistores (100 Ω gate, 10 kΩ pull-down) | Kit básico 1/4 W | Escola ou AliExpress | 8 | 0,05 € | **0,40 €** |
| 8 | Flyback diodes 1N4148 | Proteção dos MOSFETs | Escola / AliExpress | 4 | 0,05 € | **0,20 €** |
| 9 | Conector JST-PH 2.0 (par) | Fio para bateria→placa | AliExpress | 1 | 1,00 € | **1,00 €** |
| 10 | Fio silicone 22 AWG (verm/preto) | 1 m de cada | Escola / AliExpress | 1 | 2,00 € | **2,00 €** |
| 11 | Proto-board perfurada ou placa DIY | Base para montar os MOSFETs | Loja eletrónica local | 1 | 3,00 € | **3,00 €** |
| 12 | Filamento PLA (chassi + carenagem) | ~40 g; impressão na escola ou 3DHub | Escola (grátis) ou serviço | 1 | 4,00 € | **4,00 €** |
| 13 | LEDs + resistores (indicador laranja "spice") | 5 mm + 220 Ω | Escola / AliExpress | 2 | 0,10 € | **0,20 €** |
| 14 | Velcro dupla-face + abraçadeiras | Fixação bateria e IMU | Loja local | 1 | 1,50 € | **1,50 €** |
| 15 | Parafusos M2 + porcas | Montagem motores | Loja local / escola | 8 | 0,05 € | **0,40 €** |

**Total comprado: ≈ 44,30 €** ✔ dentro dos 70 € (folga de ~25 € para portes, reservas e imprevistos).

## 2. Componentes fornecidos pela escola (custo 0 €)

| Componente | Valor evitado |
|---|---|
| ESP32 devkit (WROOM-32) | ~8,00 € |
| Ferro de soldar + estanho + fluxo | ~20,00 € |
| Cabos jumpers / fio | ~2,00 € |
| Multímetro (testes) | ~10,00 € |
| **Total evitado** | **~40,00 €** |

## 3. Opcionais (se sobrar orçamento)

| Componente | Preço | Efeito |
|---|---|---|
| Barómetro BMP280 | ~2 € | Modo *height-hold* do firmware |
| Fluxo ótico PMW3901 | ~12 € | Modo *position-hold* (hover sem deriva) |
| Anel LED WS2812 | ~2 € | Efeito visual "spice" laranja |

## 4. Notas de compra

- **AliExpress:** mais barato mas 2–4 semanas de espera → encomendar **já**.
- **Amazon.es:** entrega 24–72 h, ~30 % mais caro — usar para bateria e carregador (críticos).
- **Lojas PT:** Robotshop.pt, Bricogeek (ES), lojas RC locais para bateria/hélices de reserva.
- Comprar **2 baterias** se possível: uma voa, outra carrega (a aula de demonstração fica garantida).

---

*Preços: estimativas realistas de loja (AliExpress/Amazon.es), set. 2026. Confirmar no checkout.*
