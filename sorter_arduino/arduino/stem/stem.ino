#include <Servo.h>

// Подключение сервопривода
Servo myServo;
const int servoPin = 9;

// Подключение инфракрасного дальномера Sharp 2Y0A21
const int sharpIrPin = A0;
const int numSamples = 5;

// Подключение MotorShield
#define SPEED_1 5
#define DIR_1 4
#define SPEED_2 6
#define DIR_2 7

// Флаг обнаружения объекта
bool objectDetected = false;
// Флаг для паузы перед включением моторов
bool delayApplied = false;
// Флаг для управления запуском/остановкой программы
bool programStarted = false;

void setup() {
    Serial.begin(9600);
    Serial.println("WAITING TO START...");

    // Настройка сервопривода
    myServo.attach(servoPin);
    myServo.write(90);  // Среднее положение

    // Настройка MotorShield
    for (int i = 4; i < 8; i++) {
        pinMode(i, OUTPUT);
    }
}

void loop() {
    // Обработка всех входящих команд
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();

        Serial.print("COMMAND: ");
        Serial.println(input);

        if (input == "START") {
            programStarted = true;
            Serial.println("PROGRAM STARTED");
            return;
        } else if (input == "STOP") {
            programStarted = false;
            stopMotors();
            objectDetected = false;
            Serial.println("PROGRAM STOPPED");
            return;
        }

        // Если программа не запущена — всё остальное игнорируем
        if (!programStarted) {
            Serial.println("Send 'START' to begin");
            return;
        }

        // Если программа запущена и ждём команду после обнаружения объекта
        if (objectDetected && (input == "BAD" || input == "GOOD" || input == "SKIP")) {
            stopMotors();
            moveServo(input);
            objectDetected = false;
        } else if (objectDetected) {
            Serial.println("Error: wrong command. Wait...");
        }
    }

    if (!programStarted) return;

    // Проверяем обнаружение объекта
    if (!objectDetected && isSharpIrDetected()) {
        objectDetected = true;
        delayApplied = false; // Сбрасываем флаг задержки
        Serial.println("Object detected");
    }

    // Применяем задержку перед включением моторов только один раз
    if (objectDetected && !delayApplied) {
        Serial.println("Waiting before starting motors");
        delay(2000); // Задержка перед включением моторов
        Serial.println("Starting motors");
        startMotors();
        delayApplied = true; // Устанавливаем флаг, чтобы избежать повторной задержки
    }
}

// Запуск моторов
void startMotors() {
    digitalWrite(DIR_1, LOW);
    analogWrite(SPEED_1, 250);
    digitalWrite(DIR_2, LOW);
    analogWrite(SPEED_2, 250);
}

// Остановка моторов
void stopMotors() {
    analogWrite(SPEED_1, 0);
    analogWrite(SPEED_2, 0);
    Serial.println("Motors stopped");
}

// Управление сервоприводом
void moveServo(String command) {
    if (command == "BAD") {
        myServo.write(20);
    } else if (command == "GOOD") {
        myServo.write(160);
    }
    delay(2000);
    myServo.write(90);
    delay(3000);
}

// Обнаружение объекта с помощью Sharp IR
bool isSharpIrDetected() {
    int samples[numSamples];
    for (int i = 0; i < numSamples; i++) {
        samples[i] = analogRead(sharpIrPin);
        delay(10);
    }
    // Сортировка массива (медианное сглаживание)
    for (int i = 0; i < numSamples - 1; i++) {
        for (int j = i + 1; j < numSamples; j++) {
            if (samples[i] > samples[j]) {
                int temp = samples[i];
                samples[i] = samples[j];
                samples[j] = temp;
            }
        }
    }
    int sensorValue = (samples[numSamples / 2 - 1] + samples[numSamples / 2]) / 2;
    float distance = pow((3027.4 / sensorValue), 1.2134);
    if (distance < 9) distance = 9;
    if (distance > 20) distance = 20;
    // Serial.println(distance);
    return (distance < 10);
}
