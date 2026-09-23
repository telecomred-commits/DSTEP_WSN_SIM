#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

// ============================================================
// TEST002-REAL - TX
// ESP32 DevKit V1 / ESP32 clásico
// ESP-NOW unicast + application ACK
//
// Objetivo:
//   Caracterizar el enlace físico real.
//   En Test002 NO se usan retransmisiones por defecto.
//   El RX es la fuente autoritativa para DATA PDR.
//
// Requiere Arduino-ESP32 3.x / ESP-IDF 5.1+.
// ============================================================

// ---------- CONFIGURACIÓN EXPERIMENTAL ----------
static const uint8_t WIFI_CHANNEL = 6;

// 80 unidades de 0.25 dBm -> máximo mapeado de 20 dBm en ESP32.
// Mantener fijo durante toda una campaña.
static const int8_t TX_POWER_QDBM = 80;

static const uint32_t TEST_PACKET_LIMIT = 1000;
static const uint32_t SEND_INTERVAL_MS = 100;
static const uint32_t ACK_TIMEOUT_MS = 80;

// TEST002: 0 retries para medir PDR crudo.
// TEST003: cambiar a 3 para estudiar confiabilidad/retries.
static const uint8_t MAX_RETRIES = 0;
static const uint32_t RETRY_BACKOFF_MS = 10;

// IMPORTANTE:
// 1) Flashee primero el RX.
// 2) Copie la MAC STA que imprime el RX.
// 3) Reemplace los 6 bytes siguientes.
uint8_t RX_MAC[6] = {0x24, 0x6F, 0x28, 0x00, 0x00, 0x00};

// ---------- FORMATO DE PAQUETES ----------
static const uint32_t DATA_MAGIC = 0x44535450; // "DSTP"
static const uint32_t ACK_MAGIC  = 0x41434B32; // "ACK2"
static const uint8_t MSG_DATA = 1;

#pragma pack(push, 1)
struct DataPacket {
  uint32_t magic;       // 4
  uint32_t packet_id;   // 4 -> 8
  uint32_t tx_time_us;  // 4 -> 12
  uint8_t attempt;      // 1 -> 13
  uint8_t msg_type;     // 1 -> 14
  uint16_t reserved;    // 2 -> 16
  uint8_t payload[32];  // 32 -> 48 bytes total
};

struct AckPacket {
  uint32_t magic;          // 4
  uint32_t packet_id;      // 4 -> 8
  uint32_t rx_time_us;     // 4 -> 12 (reloj local RX)
  int8_t data_rssi_dbm;    // 1 -> 13 (RSSI DATA medido en RX)
  uint8_t attempt;         // 1 -> 14
  uint16_t reserved;       // 2 -> 16 bytes total
};
#pragma pack(pop)

static_assert(sizeof(DataPacket) == 48, "DataPacket debe medir exactamente 48 bytes");
static_assert(sizeof(AckPacket) == 16, "AckPacket debe medir exactamente 16 bytes");

// ---------- EVENTO ACK ----------
struct AckEvent {
  AckPacket ack;
  int8_t ack_rssi_dbm;       // RSSI del ACK medido en TX
  uint32_t ack_rx_time_us;    // reloj local TX al recibir ACK
};

QueueHandle_t ackQueue = nullptr;

// ---------- ESTADO ----------
uint32_t currentPacketId = 0;
uint8_t currentAttempt = 0;
bool waitingAck = false;
bool retryPending = false;
bool testFinished = false;
bool summaryPrinted = false;

uint32_t logicalStartUs = 0;
uint32_t attemptSendUs[1 + 3] = {0, 0, 0, 0};
uint32_t lastNewPacketStartMs = 0;
uint32_t retryDueMs = 0;

// ---------- MÉTRICAS ----------
uint32_t logicalPacketsStarted = 0;
uint32_t ackConfirmed = 0;
uint32_t logicalUnconfirmed = 0;
uint32_t txAttempts = 0;
uint32_t retries = 0;
uint32_t appTimeouts = 0;
uint32_t espNowSendApiErrors = 0;
uint32_t staleAcks = 0;
uint32_t invalidAcks = 0;

uint64_t rttAccumUs = 0;
uint32_t rttCount = 0;
uint32_t rttMinUs = 0xFFFFFFFF;
uint32_t rttMaxUs = 0;

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

void fillPayload(DataPacket& p) {
  for (size_t i = 0; i < sizeof(p.payload); i++) {
    p.payload[i] = (uint8_t)((p.packet_id + i * 17U) & 0xFF);
  }
}

void printCsvHeader() {
  Serial.println(
    "packet_id,attempts,retries,ack_received,"
    "rssi_data_at_rx_dbm,rssi_ack_at_tx_dbm,"
    "rtt_us,e2e_us,timeout_ms,success"
  );
}

void logFinalPacket(
  bool success,
  int8_t rssiData,
  int8_t rssiAck,
  long rttUs,
  uint32_t e2eUs
) {
  Serial.print(currentPacketId); Serial.print(",");
  Serial.print((int)currentAttempt); Serial.print(",");
  Serial.print((int)(currentAttempt - 1)); Serial.print(",");
  Serial.print(success ? 1 : 0); Serial.print(",");
  Serial.print((int)rssiData); Serial.print(",");
  Serial.print((int)rssiAck); Serial.print(",");
  Serial.print(rttUs); Serial.print(",");
  Serial.print(e2eUs); Serial.print(",");
  Serial.print(ACK_TIMEOUT_MS); Serial.print(",");
  Serial.println(success ? 1 : 0);
}

// ============================================================
// ESP-NOW
// ============================================================

void onEspNowReceive(const esp_now_recv_info_t* info,
                     const uint8_t* data,
                     int len) {
  if (len != (int)sizeof(AckPacket) || !info || !data) {
    return;
  }

  AckPacket ack;
  memcpy(&ack, data, sizeof(ack));

  if (ack.magic != ACK_MAGIC) {
    return;
  }

  AckEvent evt{};
  evt.ack = ack;
  evt.ack_rssi_dbm =
    (info->rx_ctrl != nullptr) ? info->rx_ctrl->rssi : -127;
  evt.ack_rx_time_us = micros();

  // Callback Wi-Fi: no Serial, no lógica pesada.
  xQueueSend(ackQueue, &evt, 0);
}

bool addRxPeer() {
  if (esp_now_is_peer_exist(RX_MAC)) {
    return true;
  }

  esp_now_peer_info_t peer{};
  memcpy(peer.peer_addr, RX_MAC, 6);
  peer.channel = WIFI_CHANNEL;
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = false;

  esp_err_t err = esp_now_add_peer(&peer);
  if (err != ESP_OK) {
    Serial.print("# ERROR esp_now_add_peer: ");
    Serial.println((int)err);
    return false;
  }
  return true;
}

bool sendCurrentAttempt(bool isRetry) {
  if (!addRxPeer()) {
    return false;
  }

  DataPacket p{};
  p.magic = DATA_MAGIC;
  p.packet_id = currentPacketId;
  p.attempt = currentAttempt;
  p.msg_type = MSG_DATA;
  p.reserved = 0;
  p.tx_time_us = micros();
  fillPayload(p);

  uint8_t index = currentAttempt - 1;
  if (index < 4) {
    attemptSendUs[index] = p.tx_time_us;
  }

  esp_err_t err = esp_now_send(
    RX_MAC,
    reinterpret_cast<const uint8_t*>(&p),
    sizeof(p)
  );

  txAttempts++;

  if (isRetry) {
    retries++;
  }

  if (err != ESP_OK) {
    espNowSendApiErrors++;
    Serial.print("# WARN esp_now_send API error packet=");
    Serial.print(currentPacketId);
    Serial.print(" attempt=");
    Serial.print(currentAttempt);
    Serial.print(" err=");
    Serial.println((int)err);
  }

  waitingAck = true;
  retryPending = false;
  return err == ESP_OK;
}

// ============================================================
// LÓGICA TEST002
// ============================================================

void startNewLogicalPacket() {
  currentPacketId++;
  currentAttempt = 1;
  logicalStartUs = micros();

  for (auto &t : attemptSendUs) t = 0;

  logicalPacketsStarted++;
  lastNewPacketStartMs = millis();

  sendCurrentAttempt(false);
}

void finalizeFailure() {
  waitingAck = false;
  retryPending = false;
  logicalUnconfirmed++;

  uint32_t e2eUs = micros() - logicalStartUs;
  logFinalPacket(false, -127, -127, -1, e2eUs);
}

void scheduleRetry() {
  waitingAck = false;
  retryPending = true;
  retryDueMs = millis() + RETRY_BACKOFF_MS;
}

void processAckEvent(const AckEvent& evt) {
  if (evt.ack.packet_id != currentPacketId) {
    staleAcks++;
    return;
  }

  if (!waitingAck && !retryPending) {
    staleAcks++;
    return;
  }

  uint8_t ackAttempt = evt.ack.attempt;
  if (ackAttempt < 1 || ackAttempt > currentAttempt || ackAttempt > 4) {
    invalidAcks++;
    return;
  }

  uint32_t sendUs = attemptSendUs[ackAttempt - 1];
  long rttUs = -1;

  if (sendUs != 0) {
    rttUs = (long)(evt.ack_rx_time_us - sendUs);

    if ((uint32_t)rttUs < rttMinUs) rttMinUs = (uint32_t)rttUs;
    if ((uint32_t)rttUs > rttMaxUs) rttMaxUs = (uint32_t)rttUs;
    rttAccumUs += (uint32_t)rttUs;
    rttCount++;
  }

  waitingAck = false;
  retryPending = false;
  ackConfirmed++;

  uint32_t e2eUs = evt.ack_rx_time_us - logicalStartUs;

  logFinalPacket(
    true,
    evt.ack.data_rssi_dbm,
    evt.ack_rssi_dbm,
    rttUs,
    e2eUs
  );
}

void printSummary() {
  if (summaryPrinted) return;
  summaryPrinted = true;

  Serial.println();
  Serial.println("# ================= TEST002 REAL TX SUMMARY =================");
  Serial.print("# logical_packets_started = "); Serial.println(logicalPacketsStarted);
  Serial.print("# ack_confirmed           = "); Serial.println(ackConfirmed);
  Serial.print("# logical_unconfirmed     = "); Serial.println(logicalUnconfirmed);
  Serial.print("# tx_attempts             = "); Serial.println(txAttempts);
  Serial.print("# retries                 = "); Serial.println(retries);
  Serial.print("# app_timeouts            = "); Serial.println(appTimeouts);
  Serial.print("# espnow_send_api_errors  = "); Serial.println(espNowSendApiErrors);
  Serial.print("# stale_acks              = "); Serial.println(staleAcks);
  Serial.print("# invalid_acks            = "); Serial.println(invalidAcks);

  float confirmedRatio =
    (logicalPacketsStarted > 0)
      ? (float)ackConfirmed / (float)logicalPacketsStarted
      : 0.0f;

  Serial.print("# confirmed_ratio         = ");
  Serial.println(confirmedRatio, 6);

  if (rttCount > 0) {
    double meanRtt = (double)rttAccumUs / (double)rttCount;
    Serial.print("# rtt_mean_us             = "); Serial.println(meanRtt, 2);
    Serial.print("# rtt_min_us              = "); Serial.println(rttMinUs);
    Serial.print("# rtt_max_us              = "); Serial.println(rttMaxUs);
  }

  Serial.println("# NOTE: DATA PDR authoritative = calcular con el log del RX.");
  Serial.println("# ===========================================================");
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

  Serial.println("# TEST002-REAL TX");
  Serial.print("# TX STA MAC: ");
  Serial.println(WiFi.macAddress());

  Serial.print("# RX target MAC: ");
  printMac(RX_MAC);
  Serial.println();

  Serial.print("# channel: "); Serial.println(WIFI_CHANNEL);
  Serial.print("# tx_power_qdbm: "); Serial.println(TX_POWER_QDBM);
  Serial.print("# channel_set_status: "); Serial.println((int)chErr);
  Serial.print("# tx_power_set_status: "); Serial.println((int)pwrErr);
  Serial.print("# sizeof(DataPacket): "); Serial.println(sizeof(DataPacket));
  Serial.print("# max_retries: "); Serial.println(MAX_RETRIES);

  if (esp_now_init() != ESP_OK) {
    Serial.println("# FATAL: esp_now_init fallo");
    while (true) delay(1000);
  }

  ackQueue = xQueueCreate(16, sizeof(AckEvent));
  if (!ackQueue) {
    Serial.println("# FATAL: no se pudo crear ackQueue");
    while (true) delay(1000);
  }

  if (esp_now_register_recv_cb(onEspNowReceive) != ESP_OK) {
    Serial.println("# FATAL: no se pudo registrar callback RX");
    while (true) delay(1000);
  }

  if (!addRxPeer()) {
    Serial.println("# FATAL: no se pudo agregar RX como peer");
    while (true) delay(1000);
  }

  printCsvHeader();
  delay(1000);
}

void loop() {
  // Procesar ACKs recibidos
  AckEvent evt;
  while (xQueueReceive(ackQueue, &evt, 0) == pdTRUE) {
    processAckEvent(evt);
  }

  if (testFinished) {
    printSummary();
    delay(20);
    return;
  }

  uint32_t nowMs = millis();

  // Timeout de ACK del intento activo
  if (waitingAck) {
    uint8_t idx = currentAttempt - 1;
    uint32_t sentUs = (idx < 4) ? attemptSendUs[idx] : 0;

    if (sentUs != 0 &&
        (uint32_t)(micros() - sentUs) >= ACK_TIMEOUT_MS * 1000UL) {

      appTimeouts++;
      waitingAck = false;

      if ((currentAttempt - 1) < MAX_RETRIES) {
        currentAttempt++;
        scheduleRetry();
      } else {
        finalizeFailure();
      }

      return;
    }
  }

  // Retry no bloqueante
  if (retryPending && (int32_t)(nowMs - retryDueMs) >= 0) {
    sendCurrentAttempt(true);
    return;
  }

  // Nuevo paquete lógico
  if (!waitingAck && !retryPending) {
    if (logicalPacketsStarted >= TEST_PACKET_LIMIT) {
      if ((ackConfirmed + logicalUnconfirmed) >= TEST_PACKET_LIMIT) {
        testFinished = true;
        printSummary();
      }
      return;
    }

    if (logicalPacketsStarted == 0 ||
        (uint32_t)(nowMs - lastNewPacketStartMs) >= SEND_INTERVAL_MS) {
      startNewLogicalPacket();
    }
  }
}
