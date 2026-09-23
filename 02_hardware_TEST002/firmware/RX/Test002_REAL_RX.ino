#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

// ============================================================
// TEST002-REAL - RX
// ESP32 DevKit V1 / ESP32 clásico
// ESP-NOW unicast + RSSI real + application ACK
//
// Objetivo:
//   Medir DATA recibido realmente por el ESP32:
//   packet_id, RSSI, duplicados y entrega lógica.
//
// Requiere Arduino-ESP32 3.x / ESP-IDF 5.1+,
// porque RSSI se obtiene de esp_now_recv_info_t::rx_ctrl.
// ============================================================

// ---------- CONFIGURACIÓN EXPERIMENTAL ----------
static const uint8_t WIFI_CHANNEL = 6;
static const int8_t TX_POWER_QDBM = 80;

// Debe coincidir con TX para interpretar el final del experimento.
static const uint32_t EXPECTED_PACKET_LIMIT = 1000;

// ---------- FORMATO DE PAQUETES ----------
static const uint32_t DATA_MAGIC = 0x44535450; // "DSTP"
static const uint32_t ACK_MAGIC  = 0x41434B32; // "ACK2"
static const uint8_t MSG_DATA = 1;

#pragma pack(push, 1)
struct DataPacket {
  uint32_t magic;
  uint32_t packet_id;
  uint32_t tx_time_us;
  uint8_t attempt;
  uint8_t msg_type;
  uint16_t reserved;
  uint8_t payload[32];
};

struct AckPacket {
  uint32_t magic;
  uint32_t packet_id;
  uint32_t rx_time_us;
  int8_t data_rssi_dbm;
  uint8_t attempt;
  uint16_t reserved;
};
#pragma pack(pop)

static_assert(sizeof(DataPacket) == 48, "DataPacket debe medir exactamente 48 bytes");
static_assert(sizeof(AckPacket) == 16, "AckPacket debe medir exactamente 16 bytes");

// ---------- EVENTO RX ----------
struct DataEvent {
  DataPacket packet;
  int8_t rssi_dbm;
  uint32_t rx_time_us;
  uint8_t src_mac[6];
};

QueueHandle_t dataQueue = nullptr;

// ---------- MÉTRICAS ----------
uint32_t rxSampleId = 0;
uint32_t dataAttemptsReceived = 0;
uint32_t logicalDeliveredTotal = 0;
uint32_t duplicatesTotal = 0;
uint32_t invalidFrames = 0;
uint32_t queueDrops = 0;
uint32_t ackSendRequests = 0;
uint32_t ackSendApiErrors = 0;

uint32_t lastDeliveredId = 0;
uint32_t maxPacketIdSeen = 0;

int64_t rssiAccum = 0;
uint32_t rssiCount = 0;
int8_t rssiMin = 127;
int8_t rssiMax = -127;

// ============================================================
// UTILIDADES
// ============================================================

void printMac(const uint8_t* mac) {
  for (int i = 0; i < 6; i++) {
    if (i) Serial.print(":");
    if (mac[i] < 16) Serial.print("0");
    Serial.print(mac[i], HEX);
  }
}

void printCsvHeader() {
  Serial.println(
    "rx_sample_id,packet_id,attempt_no,rx_time_us,rssi_dbm,"
    "logical_delivered_now,duplicate_now,"
    "logical_delivered_total,duplicates_total"
  );
}

bool ensurePeer(const uint8_t* mac) {
  if (esp_now_is_peer_exist(mac)) {
    return true;
  }

  esp_now_peer_info_t peer{};
  memcpy(peer.peer_addr, mac, 6);
  peer.channel = WIFI_CHANNEL;
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = false;

  esp_err_t err = esp_now_add_peer(&peer);
  if (err != ESP_OK) {
    Serial.print("# WARN esp_now_add_peer failed err=");
    Serial.println((int)err);
    return false;
  }

  return true;
}

// ============================================================
// CALLBACK ESP-NOW
// ============================================================

void onEspNowReceive(const esp_now_recv_info_t* info,
                     const uint8_t* data,
                     int len) {
  if (!info || !data || len != (int)sizeof(DataPacket)) {
    invalidFrames++;
    return;
  }

  DataPacket p;
  memcpy(&p, data, sizeof(p));

  if (p.magic != DATA_MAGIC || p.msg_type != MSG_DATA) {
    invalidFrames++;
    return;
  }

  DataEvent evt{};
  evt.packet = p;
  evt.rssi_dbm =
    (info->rx_ctrl != nullptr) ? info->rx_ctrl->rssi : -127;
  evt.rx_time_us = micros();
  memcpy(evt.src_mac, info->src_addr, 6);

  // Callback Wi-Fi: solo copiar y encolar.
  if (xQueueSend(dataQueue, &evt, 0) != pdTRUE) {
    queueDrops++;
  }
}

// ============================================================
// PROCESAMIENTO
// ============================================================

void processDataEvent(const DataEvent& evt) {
  dataAttemptsReceived++;
  rxSampleId++;

  if (evt.packet.packet_id > maxPacketIdSeen) {
    maxPacketIdSeen = evt.packet.packet_id;
  }

  bool duplicate = (evt.packet.packet_id == lastDeliveredId);
  bool deliveredNow = false;

  if (duplicate) {
    duplicatesTotal++;
  } else {
    // Test002 tiene un único paquete outstanding y packet_id monotónico.
    // Por ello cualquier nuevo ID válido corresponde a una nueva entrega lógica.
    lastDeliveredId = evt.packet.packet_id;
    logicalDeliveredTotal++;
    deliveredNow = true;
  }

  if (evt.rssi_dbm != -127) {
    rssiAccum += evt.rssi_dbm;
    rssiCount++;
    if (evt.rssi_dbm < rssiMin) rssiMin = evt.rssi_dbm;
    if (evt.rssi_dbm > rssiMax) rssiMax = evt.rssi_dbm;
  }

  // CSV: una fila por DATA realmente recibido.
  Serial.print(rxSampleId); Serial.print(",");
  Serial.print(evt.packet.packet_id); Serial.print(",");
  Serial.print(evt.packet.attempt); Serial.print(",");
  Serial.print(evt.rx_time_us); Serial.print(",");
  Serial.print((int)evt.rssi_dbm); Serial.print(",");
  Serial.print(deliveredNow ? 1 : 0); Serial.print(",");
  Serial.print(duplicate ? 1 : 0); Serial.print(",");
  Serial.print(logicalDeliveredTotal); Serial.print(",");
  Serial.println(duplicatesTotal);

  // Application ACK.
  if (!ensurePeer(evt.src_mac)) {
    return;
  }

  AckPacket ack{};
  ack.magic = ACK_MAGIC;
  ack.packet_id = evt.packet.packet_id;
  ack.rx_time_us = evt.rx_time_us;
  ack.data_rssi_dbm = evt.rssi_dbm;
  ack.attempt = evt.packet.attempt;
  ack.reserved = 0;

  esp_err_t err = esp_now_send(
    evt.src_mac,
    reinterpret_cast<const uint8_t*>(&ack),
    sizeof(ack)
  );

  ackSendRequests++;

  if (err != ESP_OK) {
    ackSendApiErrors++;
    Serial.print("# WARN ACK esp_now_send API error packet=");
    Serial.print(evt.packet.packet_id);
    Serial.print(" err=");
    Serial.println((int)err);
  }
}

void printStatus() {
  Serial.println();
  Serial.println("# ---------------- TEST002 REAL RX STATUS ----------------");
  Serial.print("# max_packet_id_seen     = "); Serial.println(maxPacketIdSeen);
  Serial.print("# data_attempts_received = "); Serial.println(dataAttemptsReceived);
  Serial.print("# logical_delivered      = "); Serial.println(logicalDeliveredTotal);
  Serial.print("# duplicates             = "); Serial.println(duplicatesTotal);
  Serial.print("# invalid_frames         = "); Serial.println(invalidFrames);
  Serial.print("# queue_drops            = "); Serial.println(queueDrops);
  Serial.print("# ack_send_requests      = "); Serial.println(ackSendRequests);
  Serial.print("# ack_send_api_errors    = "); Serial.println(ackSendApiErrors);

  if (rssiCount > 0) {
    double mean = (double)rssiAccum / (double)rssiCount;
    Serial.print("# rssi_mean_dbm          = "); Serial.println(mean, 3);
    Serial.print("# rssi_min_dbm           = "); Serial.println((int)rssiMin);
    Serial.print("# rssi_max_dbm           = "); Serial.println((int)rssiMax);
  }

  // PDR correcto solo si conocemos cuántos paquetes lógicos emitió TX.
  if (maxPacketIdSeen >= EXPECTED_PACKET_LIMIT) {
    float pdr =
      (float)logicalDeliveredTotal / (float)EXPECTED_PACKET_LIMIT;

    Serial.print("# DATA_PDR               = ");
    Serial.println(pdr, 6);
  } else {
    Serial.println("# DATA_PDR               = calcular al finalizar usando 1000 TX.");
  }

  Serial.println("# ---------------------------------------------------------");
}

// ============================================================
// SETUP / LOOP
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);

  esp_wifi_set_ps(WIFI_PS_NONE);

  esp_err_t chErr =
    esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);

  esp_err_t pwrErr =
    esp_wifi_set_max_tx_power(TX_POWER_QDBM);

  Serial.println("# TEST002-REAL RX");
  Serial.print("# RX STA MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.print("# channel: "); Serial.println(WIFI_CHANNEL);
  Serial.print("# tx_power_qdbm: "); Serial.println(TX_POWER_QDBM);
  Serial.print("# channel_set_status: "); Serial.println((int)chErr);
  Serial.print("# tx_power_set_status: "); Serial.println((int)pwrErr);
  Serial.print("# sizeof(DataPacket): "); Serial.println(sizeof(DataPacket));

  if (esp_now_init() != ESP_OK) {
    Serial.println("# FATAL: esp_now_init fallo");
    while (true) delay(1000);
  }

  dataQueue = xQueueCreate(16, sizeof(DataEvent));
  if (!dataQueue) {
    Serial.println("# FATAL: no se pudo crear dataQueue");
    while (true) delay(1000);
  }

  if (esp_now_register_recv_cb(onEspNowReceive) != ESP_OK) {
    Serial.println("# FATAL: no se pudo registrar callback RX");
    while (true) delay(1000);
  }

  printCsvHeader();
}

void loop() {
  DataEvent evt;

  while (xQueueReceive(dataQueue, &evt, 0) == pdTRUE) {
    processDataEvent(evt);
  }

  // Estado periódico cada 100 paquetes observados.
  static uint32_t lastStatusAt = 0;
  if (logicalDeliveredTotal >= lastStatusAt + 100) {
    lastStatusAt = (logicalDeliveredTotal / 100) * 100;
    printStatus();
  }

  delay(1);
}
