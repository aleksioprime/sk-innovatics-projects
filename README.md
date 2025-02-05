# Проекты на Raspberry Pi совместно с другими контроллерами:

1. [Блок **Lego Mindstorms EV3**](rpi_ev3brick/README.md)
2. [Плата **Arduino Uno**](rpi_arduino/README.md)
2. [Блок **DOBOT Magician**](rpi_dobot/README.md)

## Общая подготовка среды на Raspberry Pi

### Установка Raspberry Pi OS

Скачайте и установите Raspberry Pi Imager ([ссылка](https://www.raspberrypi.com/software/))

Выберите операционную систему для вашей версии Raspberry Pi и задайте параметры:
- имя хоста `<имя>.local`;
- имя и пароль пользователя;
- SSID и пароль от точки доступа WiFi;
- включите SSH во вкладке Службы.

Документация ([ссылка]())

### Настройка после первого запуска

После установки узнайте IP-адрес платы (через роутер или подключение к дисплею по HDMI) и подключитесь к плате по SSH, используя заданный ранее имя пользователя и пароль:
```
ssh <имя пользователя>@<IP-адрес>
```

Обновите список доступных пакетов Debian Linux (если выходит ошибка, то попробуйте позже):
```
sudo apt update
```

Установите обновления для всех пакетов, которые можно обновить без удаления или замены других пакетов:
```
sudo apt upgrade -y
```

Перезагрузите устройство:
```
sudo reboot
```

### Подготовка камеры

Проверьте работу камеры:
```
sudo rpicam-hello
sudo libcamera-hello
```

Документация по библиотеке:
https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf


## Создание виртуального окружения virtualenv и установка библиотек:

Создайте виртуальное окружение:
```
python -m venv --system-site-packages ~/venv
```

Запустите виртуальное окружение
```
source ~/venv/bin/activate
```

Для деактивации виртуального окружения:
```
deactivate
```

Для удаления виртуального окружения:
```
rm -rf ~/venv
```

Установите необходимые библиотеки:
```
pip install opencv-python==4.11.0.86
pip install tflite-runtime==2.14.0
# Если необходимо, установите полную версию TensorFlow
pip install tensorflow==2.18.0
```

Переустановите NumPy (для cameralib нужна версия < 2):
```
pip install --force-reinstall numpy==1.26.4
```

### Дополнительно. Подключение компьютера к Raspberry Pi через LAN

Войдите на Raspberry Pi через WiFi по SSH и проверьте подключённые устройства:
```
ssh <имя пользователя>@<IP-адрес>
ip a
```
Обычно, встроенная сетевая карта должна называться eth0.

Для автоматической выдачи компьютеру IP-адреса от Raspberry Pi установите на ней DHCP-сервер:
```
sudo apt install isc-dhcp-server -y
```

Укажите нужный интерфейс для DHCP

Откройте файл настроек:
```
sudo nano /etc/default/isc-dhcp-server
```
Измените содержимое:
```
INTERFACESv4="eth0"
```

Измените конфигурацию DHCP

Откройте файле dhcpd.conf:
```
sudo nano /etc/dhcp/dhcpd.conf
```
Добавьте в конце файла:
```
subnet 192.168.5.0 netmask 255.255.255.0 {
    range 192.168.5.100 192.168.5.200;
    option routers 192.168.5.1;
    option domain-name-servers 8.8.8.8, 8.8.4.4;
}
```

Установите IP для сетевой карты Raspberry Pi:
```
sudo ifconfig eth0 192.168.5.1 netmask 255.255.255.0 up
```

Перезапустите DHCP-сервер:
```
sudo systemctl restart isc-dhcp-server
```

Подключите LAN кабель и переподключитесь по SSH с компьютера:
```
ssh <имя пользователя>@192.168.5.1
```