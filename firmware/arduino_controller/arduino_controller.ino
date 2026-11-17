// 실제 배선과 부품 사양을 확인한 출력만 활성화합니다.
#include <Servo.h>
#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

// 모든 값은 확인 전 제안입니다. 모터 핀에는 구동 회로의 제어 입력만 연결합니다.
constexpr bool OUTPUTS_CONFIRMED = false;
constexpr bool FAN_DRIVER_CONFIRMED = false;
constexpr bool LCD_CONFIRMED = false;
constexpr bool RGB_ACTIVE_HIGH = true;
constexpr bool FAN_ACTIVE_HIGH = true;
constexpr int RED_PIN = 3;
constexpr int GREEN_PIN = 5;
constexpr int BLUE_PIN = 6;
constexpr int SERVO_PIN = 9;
constexpr int FAN_PIN = 8;
constexpr int CURTAIN_CLOSED_ANGLE = 0;
constexpr int CURTAIN_OPEN_ANGLE = 90;
// 16x2 HD44780 호환 I2C LCD를 가정한 설정이며 실제 모델 확인이 필요합니다.
constexpr int LCD_COLUMNS = 16;
constexpr int LCD_ROWS = 2;
constexpr unsigned long SELECTION_TIMEOUT_MS = 3000;

Servo curtain;
hd44780_I2Cexp lcd;
bool lcdReady = false;
bool servoAttached = false;
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
  int level = (on == RGB_ACTIVE_HIGH) ? HIGH : LOW;
  digitalWrite(RED_PIN, level);
  digitalWrite(GREEN_PIN, level);
  digitalWrite(BLUE_PIN, level);
}

void setFan(bool on) {
  digitalWrite(FAN_PIN, (on == FAN_ACTIVE_HIGH) ? HIGH : LOW);
}

void processCommand(const char* cmd) {
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
    if (!servoAttached) {
      // attach 전에 목표를 지정해 라이브러리 기본 각도로 움직이는 것을 방지합니다.
      curtain.write(on ? CURTAIN_OPEN_ANGLE : CURTAIN_CLOSED_ANGLE);
      if (curtain.attach(SERVO_PIN) == INVALID_SERVO) {
        Serial.println("ERR,SERVO_ATTACH");
        return;
      }
      servoAttached = true;
    } else {
      curtain.write(on ? CURTAIN_OPEN_ANGLE : CURTAIN_CLOSED_ANGLE);
    }
  }
  states[target] = on ? ON : OFF;
  displayStatus();
  Serial.println("OK");
}

void setup() {
  Serial.begin(115200);
  if (OUTPUTS_CONFIRMED) {
    setLight(false);
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    states[LIGHT] = OFF;
  }
  if (FAN_DRIVER_CONFIRMED) {
    setFan(false);
    pinMode(FAN_PIN, OUTPUT);
    states[FAN] = OFF;
  }
  if (LCD_CONFIRMED) {
    int status = lcd.begin(LCD_COLUMNS, LCD_ROWS);
    lcdReady = (status == 0);
    if (lcdReady) {
      lcd.backlight();
      displayStatus();
    }
  }
}

void loop() {
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
