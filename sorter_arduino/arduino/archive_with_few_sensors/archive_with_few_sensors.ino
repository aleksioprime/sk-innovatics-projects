#include <Servo.h>

// Переключение типа датчика (измените эту переменную)
#define SENSOR_TYPE_IR_OBSTACLE 1
#define SENSOR_TYPE_ULTRASONIC 2
#define SENSOR_TYPE_SHARP_IR 3

int sensorType = SENSOR_TYPE_SHARP_IR;  // Выберите нужный тип

// Подключение сервопривода
Servo myServo;
const int servoPin = 6;

// Подключение ультразвукового дальномера
const int trigPin = 4;
const int echoPin = 5;

// Подключение IR дальномера
const int irObstaclePin = 2;

// Подключение инфракрасного дальномера
const int sharpIrPin = A0;
// Количество измерений для сглаживания
const int numSamples = 5;

// Подключение шагового двигателя (Troyka-Stepper)
const byte stepPin = 7, directionPin = 8, enablePin = 11;
// Задержка между шагами (мс)
const int speedDelay = 400;
// Шагов на полный оборот
const int stepsPerRevolution = 200;  

const int ledPin = 13;  // Встроенный светодиод

// Флаг работы шагового двигателя
bool conveyorRunning = true;
// Флаг обнаружения объекта
bool objectDetected = false;
// Счетчик оборотов шагового двигателя
int rotationCount = 0;  

void controlStepperMotor(bool enable, bool direction, int speedDelay = speedDelay);

void setup() {
  Serial.begin(9600);
  Serial.println("START PROGRAM");

  // Настройка ультразвукового дальномера
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Настройка датчика препятствия
  pinMode(irObstaclePin, INPUT);

  // Настройка сервопривода
  myServo.attach(servoPin);
  // Перемещение сервопривода в среднее положение
  myServo.write(90);  

  // Настройка шагового двигателя
  pinMode(stepPin, OUTPUT);
  pinMode(directionPin, OUTPUT);
  pinMode(enablePin, OUTPUT);
  // Выключаем мотор при старте
  digitalWrite(enablePin, LOW);  

  // Встроенный LED
  pinMode(ledPin, OUTPUT);

  // Запуск конвейера
  startConveyor();
}

void loop() {
  // Проверяем датчик только если объект еще не был обнаружен
  if (!objectDetected && isObjectDetected()) {

    // Устанавливаем флаг обнаружения объекта
    objectDetected = true;  
    // Останавливаем шаговый мотор
    stopConveyor();

    // Очищаем буфер перед ожиданием команды
    while (Serial.available() > 0) Serial.read();
  }

  // Если объект обнаружен, ждем правильную команду
  if (objectDetected) {
    if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');
      command.trim();

      Serial.print("COMMAND: ");
      Serial.println(command);

      if (command == "BAD" || command == "GOOD" || command == "SKIP") {
        moveServo(command);      // Двигаем сервопривод
        objectDetected = false;  // Сбрасываем флаг
        startConveyor();         // Возобновляем конвейер
      } else {
        Serial.println("Ошибка: неверная команда. Ожидание...");
      }
    }
  }

  if (conveyorRunning) {
    controlStepperMotor(true, HIGH);  // Двигатель работает
  }
}

// Функция управления серво
void moveServo(String command) {
    /* Если поступила команда BAD, то мотор поворачивается в начальное положение,
    если GOOD, то в конечное положение, если SKIP, то ничего не происходит
    */
    if (command == "BAD") {
        myServo.write(0);
    } else if (command == "GOOD") {
        myServo.write(180);
    }
    // Пауза
    delay(2000);
    // Возвращаем сервопривод в центр
    myServo.write(90);
    // Пауза
    delay(3000);
}

void startConveyor() {
  digitalWrite(ledPin, HIGH);
  conveyorRunning = true;
  Serial.println("START");
  controlStepperMotor(true, HIGH);
}

void stopConveyor() {
  digitalWrite(ledPin, LOW);
  conveyorRunning = false;
  Serial.println("STOP");
  controlStepperMotor(false, HIGH);
}

// Управление шаговым двигателем (постоянная работа)
void controlStepperMotor(bool enable, bool direction, int speedDelay) {
  static int stepCount = 0;
  static bool motorEnabled = false;

  if (enable && !motorEnabled) {
    analogWrite(enablePin, 255);  // Максимальная мощность
    digitalWrite(directionPin, direction);
    motorEnabled = true;
    Serial.print("Шаговый мотор запущен, скорость (мкс): ");
    Serial.println(speedDelay);
  } else if (!enable && motorEnabled) {
    digitalWrite(enablePin, LOW);
    motorEnabled = false;
    Serial.println("Шаговый мотор отключен");
    rotationCount = 0;
    return;
  }

  if (conveyorRunning) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(speedDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(speedDelay);

    stepCount++;

    if (stepCount >= stepsPerRevolution) {
      stepCount = 0;
      rotationCount++;
      Serial.print("Обороты: ");
      Serial.println(rotationCount);
    }
  }
}

// Общая функция, выбирающая нужный датчик
bool isObjectDetected() {
  if (sensorType == SENSOR_TYPE_IR_OBSTACLE) {
    return isIrObstacleDetected();
  } else if (sensorType == SENSOR_TYPE_ULTRASONIC) {
    return isUltrasonicDetected();
  } else if (sensorType == SENSOR_TYPE_SHARP_IR) {
    return isSharpIrDetected();
  }
  return false;
}

// 1. Обнаружение с помощью IR-датчика препятствий
bool isIrObstacleDetected() {
  int result = digitalRead(irObstaclePin);
  return result == LOW;  // LOW = объект обнаружен
}

// 2. Обнаружение с помощью ультразвукового датчика HC-SR04
bool isUltrasonicDetected() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;  // Преобразование в см

  Serial.print("Расстояние: ");
  Serial.print(distance);
  Serial.println(" см");

  return (distance > 0 && distance < 10);  // Если объект ближе 10 см
}

// 3. Обнаружение с помощью инфракрасного дальномера Sharp 2Y0A21
bool isSharpIrDetected() {
  int samples[numSamples];

  // Собираем несколько измерений с датчика
  for (int i = 0; i < numSamples; i++) {
    samples[i] = analogRead(sharpIrPin);
    delay(10);  // Задержка между измерениями
  }

  // Сортируем массив (медианное сглаживание)
  for (int i = 0; i < numSamples - 1; i++) {
    for (int j = i + 1; j < numSamples; j++) {
      if (samples[i] > samples[j]) {
        int temp = samples[i];
        samples[i] = samples[j];
        samples[j] = temp;
      }
    }
  }

  // Берем среднее из центральных значений массива
  int sensorValue = (samples[numSamples / 2 - 1] + samples[numSamples / 2]) / 2;

  // Преобразуем значение АЦП в напряжение (5 В / 1024 шагов)
  // float voltage = sensorValue * 0.0048828125;

  // Вычисляем расстояние по характеристике датчика
  float distance = pow((3027.4/sensorValue), 1.2134);

  // Ограничиваем диапазон (чтобы исключить неверные значения)
  if (distance < 10) distance = 10;
  if (distance > 20) distance = 20;

  // Serial.print("Sharp IR: ");
  // Serial.print(distance);
  // Serial.println(" см");

  return (distance < 11);  // Если объект ближе 11 см
}
