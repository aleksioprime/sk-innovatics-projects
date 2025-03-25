# import cv2
# import tensorflow as tf
from serial.tools import list_ports
from pydobotplus import Dobot, CustomPosition

# Vendor ID и Product ID для Silicon Labs CP210x (Dobot)
VID = 0x10C4  # Vendor ID (Silicon Labs)
PID = 0xEA60  # Product ID (CP210x UART Bridge)

def find_dobot_port():
    """Автоматически находит порт Dobot по VID и PID"""
    available_ports = list_ports.comports()

    # Вывод доступных портов для отладки
    print(f"Доступные порты: {[f'{p.device} ({p.vid}:{p.pid})' for p in available_ports]}")

    # Фильтрация по VID/PID
    dobot_port = next((p.device for p in available_ports if p.vid == VID and p.pid == PID), None)

    if not dobot_port:
        print("Ошибка: Dobot не найден! Проверьте подключение.")
        exit(1)

    print(f"Используем порт: {dobot_port}")
    return dobot_port

def initial_dobot():
    """Инициализация и управление Dobot"""
    port = find_dobot_port()

    # Подключение к Dobot
    device = Dobot(port=port)

    # Создание кастомной позиции
    pos1 = CustomPosition(x=200, y=50, z=50)

    # Перемещение в заданные координаты
    print("Перемещение в координаты (200, 50, 50)...")
    device.move_to(x=200, y=50, z=50)

    # Перемещение в кастомную позицию
    print("Перемещение в заранее заданную позицию pos1...")
    device.move_to(position=pos1)

    # Управление конвейером
    print("Запуск конвейера со скоростью 0.5...")
    device.conveyor_belt(speed=0.5, direction=1)

    print("Перемещение объекта на конвейере со скоростью 50 мм/с, на 200 мм...")
    device.conveyor_belt_distance(speed_mm_per_sec=50, distance_mm=200, direction=1)

    print("Завершение работы и закрытие соединения...")
    device.close()


if __name__ == '__main__':
    # Для отладки версий OpenCV и TensorFlow
    # print(f"OpenCV version: {cv2.__version__}")
    # print(f"TensorFlow version: {tf.__version__}")

    initial_dobot()
