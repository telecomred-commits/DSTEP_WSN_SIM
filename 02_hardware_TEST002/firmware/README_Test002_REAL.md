# Test002-REAL — ESP32 DevKit V1

## Propósito
Esta versión sustituye la capa MQTT/canal sintético de Wokwi por un enlace ESP-NOW físico.

**Test002 mide el enlace real.**
No genera BER, fading ni RSSI artificiales.

## Requisito de software
Usar Arduino-ESP32 3.x / ESP-IDF 5.1 o posterior para leer RSSI directamente desde:

`esp_now_recv_info_t -> rx_ctrl -> rssi`

## Configuración inicial
- Hardware: 2 × ESP32 DevKit V1 / ESP32 clásico
- Canal Wi-Fi: 6
- TX power configurada: 80 unidades de 0.25 dBm (máximo mapeado 20 dBm)
- DATA ESP-NOW body: exactamente 48 bytes
- ACK de aplicación: 16 bytes
- Paquetes lógicos: 1000
- Intervalo entre paquetes: 100 ms
- ACK timeout: 80 ms
- Retries en Test002: 0
- Power save: desactivado durante la prueba

## Orden correcto

### 1. Flashear RX
Abra `RX/Test002_REAL_RX.ino`.

Al iniciar debe imprimir algo parecido a:

`# RX STA MAC: AA:BB:CC:DD:EE:FF`

Copie esa MAC.

### 2. Configurar TX
Abra `TX/Test002_REAL_TX.ino`.

Cambie:

```cpp
uint8_t RX_MAC[6] = {0x24, 0x6F, 0x28, 0x00, 0x00, 0x00};
```

por la MAC real del receptor.

Ejemplo para `AA:BB:CC:DD:EE:FF`:

```cpp
uint8_t RX_MAC[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
```

### 3. Flashear TX
Abra ambos monitores seriales a 115200.

Inicie primero RX y luego TX.

## Qué mide cada lado

### RX — fuente autoritativa de DATA PDR
El RX imprime una fila por DATA que realmente llegó:

- packet_id
- attempt_no
- rx_time_us local
- RSSI real del DATA
- entrega lógica
- duplicado

Para Test002, donde no hay retries:

`DATA_PDR = unique_DATA_received / 1000`

Ésta es la métrica principal.

### TX
El TX recibe un ACK de aplicación y registra:

- RSSI del DATA medido por RX
- RSSI del ACK medido por TX
- RTT
- confirmación

`confirmed_ratio` puede ser menor que DATA PDR si DATA llegó pero el ACK se perdió.

## Muy importante sobre latencia
No restar `tx_time_us` del TX contra `rx_time_us` del RX.
Los relojes `micros()` de dos ESP32 independientes no están sincronizados.

El firmware mide RTT en el TX con un solo reloj, lo cual sí es válido.

## Protocolo experimental sugerido
Para cada distancia:

- 1 m
- 5 m
- 10 m
- 20 m
- 30 m
- 40 m

hacer 3 repeticiones de 1000 paquetes.

Mantener:
- misma altura
- misma orientación
- mismas placas
- mismo canal
- misma TX power
- mismo intervalo
- misma ubicación relativa salvo la distancia
- línea de vista para esta primera campaña

Guardar TX y RX por separado para cada corrida.

Ejemplo:

`D01m_R1_TX.csv`
`D01m_R1_RX.csv`

## Test003
Cuando terminemos Test002, para habilitar retransmisiones físicas:

```cpp
static const uint8_t MAX_RETRIES = 3;
```

en el TX.

No modificarlo todavía para Test002.
