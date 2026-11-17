// 실제 배선과 부품 사양을 확인한 출력만 활성화합니다.
#include <Wire.h>
#include <Servo.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

// 모든 값은 확인 전 제안입니다. 모터 핀에는 구동 회로의 제어 입력만 연결합니다.
constexpr bool OUTPUTS_CONFIRMED = true;
constexpr bool FAN_DRIVER_CONFIRMED = true;
constexpr bool LCD_CONFIRMED = true;
constexpr bool LIGHT_ACTIVE_HIGH = true;
constexpr int LIGHT_PIN = 3;
constexpr int SERVO_PIN = 9;
constexpr int FAN_STEPPER_PINS[] = {10, 11, 12, 13}; // IN1, IN2, IN3, IN4
// 실제 서보와 커튼 기구의 안전한 범위를 확인한 후 조정합니다.
constexpr int CURTAIN_CLOSED_ANGLE = 0;
constexpr int CURTAIN_OPEN_ANGLE = 90;
constexpr unsigned long STEPPER_INTERVAL_MS = 3;
// 16x2 HD44780 호환 I2C LCD를 가정한 설정이며 실제 모델 확인이 필요합니다.
constexpr int LCD_COLUMNS = 16;
constexpr int LCD_ROWS = 2;
constexpr unsigned long SELECTION_TIMEOUT_MS = 3000;

hd44780_I2Cexp lcd;
Servo curtain;
bool lcdReady = false;
bool servoAttached = false;
bool fanRunning = false;
int stepIndex = 0;
unsigned long lastStep = 0;
const byte stepSequence[8] = {0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001};
enum Device { NONE, LIGHT, CURTAIN, FAN };
enum State { UNKNOWN, OFF, ON };
Device selected = NONE;
State states[] = {UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN};
unsigned long lastSelection = 0;
char line[40];
size_t used = 0;
bool overflowed = false;

const char* deviceName(Device device) {
  switch (device) {
    case LIGHT: return "LIGHT";
    case CURTAIN: return "CURTAIN";
    case FAN: return "FAN";
    default: return "NONE";
  }
}

void displayStatus() {
  if (!lcdReady) return;
  lcd.setCursor(0, 0);
  lcd.print("SEL:");
  lcd.print(deviceName(selected));
  lcd.print("           ");
  lcd.setCursor(0, 1);
  lcd.print("CMD:");
  if (selected == NONE || states[selected] == UNKNOWN) lcd.print("-- ");
  else if (states[selected] == ON) lcd.print("ON ");
  else lcd.print("OFF");
  lcd.print("         ");
}

void setLight(bool on) {
  digitalWrite(LIGHT_PIN, (on == LIGHT_ACTIVE_HIGH) ? HIGH : LOW);
}

void updateFan() {
  if (!FAN_DRIVER_CONFIRMED || !fanRunning || millis() - lastStep < STEPPER_INTERVAL_MS) return;
  lastStep = millis();
  stepIndex = (stepIndex + 1) % 8;
  for (int i = 0; i < 4; ++i) digitalWrite(FAN_STEPPER_PINS[i], (stepSequence[stepIndex] >> i) & 1);
}

void setFan(bool on) {
  fanRunning = on;
  if (!on) for (int i = 0; i < 4; ++i) digitalWrite(FAN_STEPPER_PINS[i], LOW);
}

bool scanI2c(bool report) {
  bool found = false;
  if (report) Serial.print("I2C");
  for (byte address = 8; address < 120; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      found = true;
      if (report) {
        Serial.print(',');
        if (address < 16) Serial.print('0');
        Serial.print(address, HEX);
      }
    }
    if (Wire.getWireTimeoutFlag()) {
      Wire.clearWireTimeoutFlag();
      if (report) Serial.print(",BUS_TIMEOUT");
      break;
    }
  }
  if (report) Serial.println();
  return found;
}

void processCommand(const char* cmd) {
  if (strcmp(cmd, "DIAG,LCD") == 0) {
    Serial.println(lcdReady ? "LCD,READY" : "LCD,NOT_READY");
    return;
  }
  if (strcmp(cmd, "DIAG,I2C") == 0) {
    scanI2c(true);
    return;
  }
  if (strncmp(cmd, "SELECT,", 7) == 0) {
    const char* name = cmd + 7;
    Device next;
    if (strcmp(name, "NONE") == 0) next = NONE;
    else if (strcmp(name, "LIGHT") == 0) next = LIGHT;
    else if (strcmp(name, "CURTAIN") == 0) next = CURTAIN;
    else if (strcmp(name, "FAN") == 0) next = FAN;
    else { Serial.println("ERR,UNSUPPORTED"); return; }
    bool changed = selected != next;
    selected = next;
    lastSelection = millis();
    if (changed) displayStatus();
    Serial.println("OK");
    return;
  }

  Device target = NONE;
  bool on = false;
  if (strcmp(cmd, "LIGHT,ON") == 0) { target = LIGHT; on = true; }
  else if (strcmp(cmd, "LIGHT,OFF") == 0) { target = LIGHT; }
  else if (strcmp(cmd, "CURTAIN,OPEN") == 0) { target = CURTAIN; on = true; }
  else if (strcmp(cmd, "CURTAIN,CLOSE") == 0) { target = CURTAIN; }
  else if (strcmp(cmd, "FAN,START") == 0) { target = FAN; on = true; }
  else if (strcmp(cmd, "FAN,STOP") == 0) { target = FAN; }
  else { Serial.println("ERR,UNSUPPORTED"); return; }

  if (selected != NONE && millis() - lastSelection > SELECTION_TIMEOUT_MS) {
    selected = NONE;
    displayStatus();
  }
  if (selected != target) { Serial.println("ERR,NOT_SELECTED"); return; }
  if (target == FAN && !FAN_DRIVER_CONFIRMED) {
    Serial.println("ERR,FAN_NOT_CONFIGURED");
    return;
  }
  if (target != FAN && !OUTPUTS_CONFIRMED) {
    Serial.println("ERR,OUTPUTS_NOT_CONFIGURED");
    return;
  }
  if (target == LIGHT) setLight(on);
  else if (target == FAN) setFan(on);
  else {
    int angle = on ? CURTAIN_OPEN_ANGLE : CURTAIN_CLOSED_ANGLE;
    if (!servoAttached) {
      // attach 전에 목표를 설정해 기본 각도로 먼저 움직이지 않도록 합니다.
      curtain.write(angle);
      if (curtain.attach(SERVO_PIN) == INVALID_SERVO) {
        Serial.println("ERR,SERVO_ATTACH");
        return;
      }
      servoAttached = true;
    } else {
      curtain.write(angle);
    }
  }
  states[target] = on ? ON : OFF;
  displayStatus();
  Serial.println("OK");
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  // 배선 오류로 I2C 버스가 응답하지 않아도 무한 대기하지 않도록 합니다.
  Wire.setWireTimeout(25000, true);
  if (OUTPUTS_CONFIRMED) {
    setLight(false);
    pinMode(LIGHT_PIN, OUTPUT);
    states[LIGHT] = OFF;
  }
  if (FAN_DRIVER_CONFIRMED) {
    setFan(false);
    for (int i = 0; i < 4; ++i) pinMode(FAN_STEPPER_PINS[i], OUTPUT);
    states[FAN] = OFF;
  }
  if (LCD_CONFIRMED && scanI2c(false)) {
    int status = lcd.begin(LCD_COLUMNS, LCD_ROWS);
    lcdReady = (status == 0);
    if (lcdReady) {
      lcd.backlight();
      displayStatus();
    }
  }
}

void loop() {
  updateFan();
  while (Serial.available()) {
    char c = static_cast<char>(Serial.read());
    if (c == '\r') continue;
    if (c == '\n') {
      if (overflowed) Serial.println("ERR,TOO_LONG");
      else {
        line[used] = '\0';
        processCommand(line);
      }
      used = 0;
      overflowed = false;
    } else if (!overflowed) {
      if (used + 1 < sizeof(line)) line[used++] = c;
      else overflowed = true;
    }
  }
  if (selected != NONE && millis() - lastSelection > SELECTION_TIMEOUT_MS) {
    selected = NONE;
    displayStatus();
  }
}
