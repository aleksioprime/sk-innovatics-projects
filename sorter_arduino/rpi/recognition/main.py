import io
import os
import cv2
import logging
import argparse
import socketserver
import threading
import serial
import time
import glob
import subprocess
import numpy as np
from threading import Condition
from collections import Counter
from http import server
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from libcamera import Transform
from tflite_runtime.interpreter import Interpreter


class Config:
    """
    Конфигурационный класс, содержащий пути к файлам модели, меткам и шаблону HTML
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "data", "model.tflite")
    LABELS_PATH = os.path.join(BASE_DIR, "data", "labels.csv")
    HTML_TEMPLATE_PATH = os.path.join(BASE_DIR, "template", "index.html")
    PORT = 8000
    BUFFER_SIZE = 50
    CROP_SIZE = 400             # Размер квадратного изображения
    CROP_OFFSET_X = 0           # Смещение по горизонтали от центра (в пикселях)
    CROP_OFFSET_Y = -40         # Смещение по вертикали от центра (в пикселях)


class FrameCollector(threading.Thread):
    """
    Фоновый поток для сбора кадров, распознавания и аннотирования изображений
    """
    def __init__(self, classifier, buffer):
        super().__init__()
        self.classifier = classifier
        self.frames_buffer = buffer
        self.running = True
        self.last_annotated_frame = None  # Последний обработанный кадр

    def run(self):
        while self.running:
            try:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame

                frame_array = np.frombuffer(frame, dtype=np.uint8)
                frame_image = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

                if frame_image is None:
                    logging.warning("Failed to decode frame")
                    continue

                frame_image = self.crop_center_square(frame_image)

                global collecting_active

                if collecting_active:
                    predictions = self.classifier.classify(frame_image)

                    if predictions:
                        best_class = predictions[0][0]
                        self.frames_buffer.append(best_class)

                        global last_classification_result
                        last_classification_result = best_class

                        if len(self.frames_buffer) > Config.BUFFER_SIZE:
                            self.frames_buffer.pop(0)

                        print(f"[DEBUG] Buffer: {self.frames_buffer}")

                    annotated = self.classifier.annotate_image(frame_image.copy(), predictions)
                else:
                    # Просто выводим "чистое" изображение без текста
                    annotated = frame_image

                self.last_annotated_frame = annotated

            except Exception as e:
                logging.error(f"Frame collection error: {e}")

            time.sleep(0.1)  # Минимальная задержка, чтобы избежать перегрузки процессора

    def crop_center_square(self, image):
        """
        Обрезает изображение в квадрат с заданным размером и смещением от центра.
        """
        h, w, _ = image.shape
        size = Config.CROP_SIZE
        offset_x = Config.CROP_OFFSET_X
        offset_y = Config.CROP_OFFSET_Y

        center_x = w // 2 + offset_x
        center_y = h // 2 + offset_y

        x1 = max(0, center_x - size // 2)
        y1 = max(0, center_y - size // 2)
        x2 = min(w, x1 + size)
        y2 = min(h, y1 + size)

        if x2 - x1 < size:
            x1 = max(0, x2 - size)
        if y2 - y1 < size:
            y1 = max(0, y2 - size)

        return image[y1:y2, x1:x2]



class ArduinoHandler(threading.Thread):
    """
    Класс для взаимодействия с Arduino через последовательный порт
    """
    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = True
        self.frames_buffer = []  # Хранение последних 10 предсказаний
        self.find_arduino()

    def find_arduino(self, retries=10):
        """Ищем Arduino, пробуем подключиться"""
        attempt = 0
        while attempt < retries:
            available_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')  # Поиск всех доступных портов
            for port in available_ports:
                try:
                    if self.ser:  # Если соединение было открыто ранее, закрываем его
                        self.ser.close()
                    self.ser = serial.Serial(port, 9600, timeout=1)
                    logging.info(f"Connected to Arduino on {port}")
                    return
                except serial.SerialException:
                    continue  # Пробуем следующий порт

            attempt += 1
            logging.warning(f"Arduino not found. Retrying in 5 seconds... ({attempt}/{retries})")
            time.sleep(5)

        logging.error("Failed to connect to Arduino after multiple attempts. Trying USB reset...")
        self.reset_usb()

    def reset_usb(self):
        """Сброс USB-порта в Linux (работает только с правами sudo)"""
        try:
            subprocess.run(["sudo", "usbreset", "$(lsusb | grep Arduino | awk '{print $6}')"], check=True)
            logging.info("USB port reset successfully. Retrying connection...")
            time.sleep(3)
            self.find_arduino()
        except Exception as e:
            logging.error(f"USB reset failed: {e}")

    def recognize_frames(self):
        """
        Функция распознавания кадров.
        Анализирует 10 последних предсказаний и возвращает преобладающий класс
        """
        if len(self.frames_buffer) < Config.BUFFER_SIZE:
            logging.warning("Not enough data for analysis")
            return 'RETURN'  # Недостаточно данных для анализа

        most_common_class = Counter(self.frames_buffer).most_common(1)[0][0]
        print(f"Most common class: {most_common_class}")
        return most_common_class

    def run(self):
        """
        Запуск потока, который слушает сообщения от Arduino и отвечает на них.
        При отключении устройства пытается переподключиться.
        """
        global collecting_active

        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    message = self.ser.readline().decode('utf-8').strip()
                    logging.info(f"Arduino message: {message}")

                    # Добавляем в лог только если сообщение новое
                    global arduino_log_messages
                    if not arduino_log_messages or arduino_log_messages[-1] != message:
                        arduino_log_messages.append(message)
                    # Ограничиваем размер лога (например, последние 20 сообщений)
                    if len(arduino_log_messages) > 20:
                        arduino_log_messages.pop(0)

                    # Если пришла команда от Arduino — запускаем сбор
                    if message == 'Starting motors':
                        collecting_active = True
                        logging.info("Frame collection started")

                # Если сбор активен и буфер заполнился — анализ и отправка
                if collecting_active and len(self.frames_buffer) >= Config.BUFFER_SIZE:
                    result = self.recognize_frames()
                    logging.info(f"Result recognition: {result}")

                    if result == 'good':
                        self.ser.write("GOOD".encode('utf-8'))
                    elif result == 'bad':
                        self.ser.write("BAD".encode('utf-8'))
                    else:
                        self.ser.write("SKIP".encode('utf-8'))

                    # После отправки — сброс
                    self.frames_buffer.clear()
                    collecting_active = False
                    logging.info("Frame collection stopped and buffer cleared")

            except (serial.SerialException, OSError) as e:
                logging.error(f"Serial error: {e}. Closing port and reconnecting...")
                if self.ser:
                    self.ser.close()
                    self.ser = None
                time.sleep(2)  # Даем системе время обработать отключение
                self.find_arduino()


    def stop(self):
        """
        Остановка потока.
        """
        self.running = False
        if self.ser:
            self.ser.close()


class Classifier:
    """
    Класс классификатора, использующий TensorFlow Lite для обработки изображений
    """
    def __init__(self, model_path, labels_path):
        # Добавляем блокировку для потокобезопасности
        self.lock = threading.Lock()

        # Загружаем модель и выделяем память
        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        # Получаем информацию о входных данных модели
        input_details = self.interpreter.get_input_details()[0]
        self.input_index = input_details['index']
        _, self.height, self.width, _ = input_details['shape']

        # Получаем информацию о выходных данных модели
        output_details = self.interpreter.get_output_details()[0]
        self.output_index = output_details['index']
        self.output_dtype = output_details['dtype']
        self.output_scale, self.output_zero_point = output_details['quantization']

        logging.info(f"Model input shape: {self.width}x{self.height}")

        # Загружаем метки классов
        with open(labels_path, 'r', encoding='utf-8') as f:
            self.labels = [line.split(",")[1].strip() for line in f]

    def process_image(self, image):
        """
        Предобработка изображения перед подачей в нейросеть
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        processed_image = cv2.resize(rgb_image, (self.width, self.height), interpolation=cv2.INTER_AREA)
        processed_image = (processed_image.astype(np.float32) / 127.5) - 1
        return processed_image

    def classify(self, image, top_k=1):
        """
        Классификация изображения
        """
        processed_image = self.process_image(image)

        # Добавляем размерность канала
        input_data = np.expand_dims(processed_image, axis=0).astype(np.float32)

        with self.lock:  # Используем блокировку при работе с моделью
            self.interpreter.set_tensor(self.input_index, input_data)
            self.interpreter.invoke()
            output = np.squeeze(self.interpreter.get_tensor(self.output_index))

        # Применяем масштабирование, если выходной формат uint8
        if self.output_dtype == np.uint8:
            output = self.output_scale * (output - self.output_zero_point)

        # Сортируем и выбираем топ-K предсказаний
        ordered = np.argsort(-output)[:top_k]

        return [(self.labels[i], output[i]) for i in ordered if output[i] > 0.01]


    def annotate_image(self, image, predictions):
        """
        Добавление аннотаций к изображению
        """
        for i, (label, score) in enumerate(predictions):
            cv2.putText(image, f"{label}: {score:.2f}", (10, 30 + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return image


class StreamingOutput(io.BufferedIOBase):
    """
    Класс для управления потоковым выводом с камеры.
    Хранит последний кадр и предоставляет механизм ожидания новых кадров.
    """
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        """
        Записывает новый кадр в буфер и уведомляет всех ожидающих клиентов
        """
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    """
    HTTP-обработчик запросов, обеспечивающий потоковую передачу видео и HTML-страницы
    """
    def do_GET(self):
        """Обрабатывает HTTP GET-запросы"""

        if self.path in ['/', '/index.html']:
            self.respond_with_html()
        elif self.path == '/stream.mjpg':
            self.stream_video()
        elif self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        elif self.path.startswith("/serial/send"):
            self.handle_serial_send()
        elif self.path.startswith("/serial/log"):
            self.handle_serial_log()
        elif self.path.startswith("/classification/buffer"):
            self.handle_buffer_status()
        elif self.path.startswith("/classification/result"):
            self.handle_classification_result()
        elif self.path.startswith("/collection/status"):
            self.handle_collection_status()
        else:
            self.send_error(404)
            self.end_headers()

    def handle_collection_status(self):
        global collecting_active
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        import json
        self.wfile.write(json.dumps({
            "active": collecting_active
        }).encode('utf-8'))

    def handle_buffer_status(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        import json
        buffer_contents = arduino_handler.frames_buffer
        counter = Counter(buffer_contents)
        self.wfile.write(json.dumps({
            "counts": counter
        }).encode('utf-8'))

    def respond_with_html(self):
        """Отправляет HTML-страницу клиенту"""
        try:
            with open(Config.HTML_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
                content = file.read().encode('utf-8')
        except FileNotFoundError:
            content = b"<html><body><h1>Error: Template not found.</h1></body></html>"
            logging.error("HTML template not found.")

        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)

    def handle_classification_result(self):
        """Возвращает последний результат классификации"""
        global last_classification_result
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        import json
        self.wfile.write(json.dumps({"recognized": last_classification_result}).encode('utf-8'))

    def handle_serial_send(self):
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        command = query.get("cmd", [None])[0]

        if command and arduino_handler.ser:
            try:
                arduino_handler.ser.write((command + "\n").encode('utf-8'))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"Sent: {command}".encode('utf-8'))
                return
            except Exception as e:
                logging.error(f"Failed to send command: {e}")

        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"Error: command not sent")

    def handle_serial_log(self):
        global arduino_log_messages
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        import json
        self.wfile.write(json.dumps({"messages": arduino_log_messages}).encode('utf-8'))

    def stream_video(self):
        """Запускает потоковую передачу видео MJPEG"""
        self.send_response(200)
        self.send_header('Age', 0)
        self.send_header('Cache-Control', 'no-cache, private')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
        self.end_headers()

        try:
            while True:
                # Ожидаем новый обработанный кадр
                if frame_collector.last_annotated_frame is None:
                    time.sleep(0.1)  # Если еще нет кадров, ждем
                    continue

                annotated_frame = frame_collector.last_annotated_frame
                _, jpeg_frame = cv2.imencode('.jpg', annotated_frame)

                try:
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(jpeg_frame))
                    self.end_headers()
                    self.wfile.write(jpeg_frame.tobytes())
                    self.wfile.write(b'\r\n')
                except (BrokenPipeError, ConnectionResetError):
                    logging.warning(f"Client disconnected: {self.client_address}")
                    break

        except Exception as e:
            logging.error(f"Error: {str(e)}")


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """HTTP-сервер, поддерживающий многопоточное соединение"""
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Raspberry Pi Camera Server")
    parser.add_argument("--flip", choices=["none", "h", "v", "hv"], default="none",
                        help="Set flip mode: 'none' (default), 'h' (horizontal), 'v' (vertical), 'hv' (both)")
    args = parser.parse_args()

    # Глобальные переменные
    collecting_active = False
    arduino_log_messages = []
    last_classification_result = "-"

    # Инициализируем ArduinoHandler в отдельном потоке
    arduino_handler = ArduinoHandler()
    arduino_handler.start()

    # Инициализируем классификатор и камеру
    classifier = Classifier(model_path=Config.MODEL_PATH, labels_path=Config.LABELS_PATH)

    # Инициализируем камеру и настраиваем ее
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(
        main={"size": (640, 480)},
        transform=Transform(hflip="h" in args.flip, vflip="v" in args.flip)))

    # Запускаем потоковый вывод с камеры
    output = StreamingOutput()
    picam2.start_recording(JpegEncoder(), FileOutput(output))

    # Запускаем фоновый поток сбора кадров
    frame_collector = FrameCollector(classifier, arduino_handler.frames_buffer)
    frame_collector.start()

    # Запускаем HTTP-сервер
    try:
        server_address = ('', Config.PORT)
        httpd = StreamingServer(server_address, StreamingHandler)
        logging.info(f"Server started on port {Config.PORT}")
        httpd.serve_forever()
    finally:
        picam2.stop_recording()
        arduino_handler.stop()
        arduino_handler.join()
        frame_collector.running = False
        frame_collector.join()
