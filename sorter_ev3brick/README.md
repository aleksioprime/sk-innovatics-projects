# Программы для проекта с использованием Raspberry Pi и Arduino

[Вернуться на главный README](../README.md)

## Подготовка EV3

Скачайте дистрибутив операционной системы [ev3dev](https://www.ev3dev.org/docs/getting-started/#step-1-download-the-latest-ev3dev-image-file)

Залейте образ на SD-карту с помощью [Win32 Disk Imager](https://sourceforge.net/projects/win32diskimager/) или [Balena Etcher](https://etcher.balena.io/)

Вставьте SD-карту в блок Lego Mindstorms EV3 и включите его

Для подключения к WiFI необходимо WiFi-адаптер. Настроить подключение к WiFi можно с помощью встроенных инструментов блока EV3. Подключаться по SSH можно с использованием имени `robot` и пароля `maker`

## Подключение EV3 к Raspberry Pi

Подключите через miniUSB кабель от блока EV3 к плате Rapsberry Pi:

Войдите на Raspberry Pi через WiFi по SSH и проверьте подключённые устройства:
```
ssh <имя пользователя>@<IP-адрес>
ip a
```
Обычно, дополнительное сетевое устройство называется eth1.

Назначьте IP этому устройству:
```
sudo ifconfig eth1 192.168.3.1 netmask 255.255.255.0 up
```

Войдите на EV3 через WiFI по SSH (пароль `maker`) и посмотрите подключённые устройства:
```
ssh robot@<IP-адрес>
ip a
```
Подключённое устройство должно называться usb1.

Назначьте IP-адрес этому устройству:
```
sudo ifconfig usb1 192.168.3.2 netmask 255.255.255.0 up
```

Проверьте подключение из Raspberry Pi на EV3:
```
ping 192.168.3.2
```

Подключитесь из Raspberry Pi на EV3 через SSH (пароль `maker`):
```
ssh robot@192.168.3.2
```

## Запуск программ

Скачайте репозиторий:
```
git clone https://github.com/aleksioprime/innoprojects.git
cd innoprojects
```

Или загрузите его архив:
```
wget https://github.com/aleksioprime/innoprojects/archive/refs/heads/main.zip
unzip main.zip
rm main.zip
cd innoprojects-main
```

### Загрузка программы на EV3

Скопируйте программу на Raspberry:
```
scp -r sorter_ev3brick/ev3/* <имя пользователя>@<IP-адрес>:ev3
```

Зайдите по SSH на Raspberry и скопируйте программу на EV3:
```
ssh <имя пользователя>@<IP-адрес>
cd ev3
scp -r server.py robot@192.168.3.2:/home/robot/
```

### Загрузка программы на Raspberry Pi:

Загрузите программу на микрокомпютер через SFTP-приложения или с помощью команды терминала:

```
scp -r sorter_ev3brick/rpi/* <имя пользователя>@<IP-адрес>:app
```

Если вы изменяете программу и выгружаете снова, то можно использовать следующую команду:
```
rsync -av sorter_ev3brick/rpi/* <имя пользователя>@<IP-адрес>:app
```

### Запуск программ

Подключитесь к Raspberry Pi по SSH через SSH-приложение или с помощью команды терминала:
```
ssh <имя пользователя>@<IP-адрес>
```

Запустите виртуальное окружение
```
source ~/venv/bin/activate
```

Запустите программу на EV3 через Raspberry:
```
ssh robot@192.168.3.2 "python3 /home/stem/main.py"
```

Запустите программу на Raspberry:
```
python app/main.py
```