import time
import pydobot

# Подключаемся к Dobot через порт USB
port = "/dev/ttyUSB0"  # Проверьте через `ls /dev/ttyUSB*`
device = pydobot.Dobot(port=port, verbose=True)

# Двигаем робота в разные позиции
device.move_to(200, 0, -50, 0)
time.sleep(2)

device.move_to(150, 150, -50, 0)
time.sleep(2)

device.move_to(100, -150, -50, 0)
time.sleep(2)

# Завершаем соединение
device.close()