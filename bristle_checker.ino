// ===== Brush Zig-Zag Detection Indicator =====
// PASS LED -> Green, connected to pin 8
// FAIL LED -> Red, connected to pin 9

const int passLED = 8;
const int failLED = 9;

void setup() {
  pinMode(passLED, OUTPUT);
  pinMode(failLED, OUTPUT);

  Serial.begin(9600); // Must match Python baud rate
}

void loop() {
  if (Serial.available() > 0) {
    char result = Serial.read();

    if (result == 'P') {
      // PASS condition
      digitalWrite(passLED, HIGH);
      digitalWrite(failLED, LOW);
    }
    else if (result == 'F') {
      // FAIL condition
      digitalWrite(passLED, LOW);
      digitalWrite(failLED, HIGH);
    }
  }
}
