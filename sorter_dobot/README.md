# Программы для проекта сортировщика с использованием Raspberry Pi и Dobot Magician

[Вернуться на главный README](../README.md)

Программы предназначены для запуска на ОС Linux Ubuntu

## Установка Linux

Скачайте и установите Linux Ubuntu Desktop Image на компьютер:

- Ubuntu 22.04.5 LTS (Jammy Jellyfish) ([ссылка](https://releases.ubuntu.com/22.04/))
- Ubuntu 24.04.1 (Noble Numbat) ([ссылка](https://releases.ubuntu.com/24.04/))

Инструкция по установке: [https://ubuntu.com/tutorials/install-ubuntu-desktop](https://ubuntu.com/tutorials/install-ubuntu-desktop)

## Подготовка окружения

Установите CURL:
```sh
sudo apt install curl
```

Установите GIT
```sh
sudo apt install git -y
```

### Установка и настройка PyEnv

Источник: [ссылка](https://github.com/pyenv/pyenv)

Установите pyenv
```sh
curl -fsSL https://pyenv.run | bash
```

Добавьте настройки в bashrc
```sh
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --patch)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
```

Альтернативный вариант.
Откройте файл для редактирования:
```sh
sudo nano ~/.bashrc
```

Вставьте в конец файла следующие строчки:
```
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

Примените изменения:
```sh
source ~/.bashrc
```

Проверьте версию pyenv:
```sh
pyenv --version
```

### Установка зависимостей для Linux

Установите пакеты среды:
```sh
sudo apt install -y libbz2-dev libnsurses-dev libffi-dev libreadline-dev libssl-dev libsqlite3-dev tk-dev liblzma-dev
```

Полный список зависимостей [источник](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)
```sh
sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl git \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

### Создание виртуальной среды окружения

Проверьте установленные плагины:
```sh
pyenv --version
pyenv virtualenvs
```

Установите версию Python:
```sh
pyenv install 3.10.16
```

Создайте виртуальное окружение:
```sh
pyenv virtualenv 3.10.16 trash
```

Активация виртуального окружения:
```sh
pyenv activate trash
```

Выход из виртуального окружения:
```sh
pyenv deactivate
```

### Установка драйвера и настройка доступа

Установите драйвер [VCP](https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers) (если потребуется)
Подключите Dobot Magician и проверьте подключение USB:
```
lsusb
```

Если адаптер CP210x распознан, вы увидите строку, например:
```
Bus 001 Device 003: ID 10c4:ea60 Silicon Labs CP210x UART Bridge
```

Если в процессе запуска программ выходит ошибка `Permission denied: '/dev/ttyUSB0'`, то у вашего пользователя нет прав на доступ к порту `/dev/ttyUSB0`.

Чтобы это исправить необходимо выполнить команду `sudo usermod -a -G dialout $USER`, чтобы убедиться, что доступ к `/dev/ttyUSB0` есть только у пользователей в группе `dialout`.

Добавьте текущего пользователя в эту группу:
```
sudo usermod -a -G dialout $USER
```
Затем перезапустите систему.

Временное решение (эта команда даст всем пользователям доступ к порту, но пропадёт после перезагрузки):
```
sudo chmod 666 /dev/ttyUSB0
```


### Установка необходимых библиотек

Обновите PIP:
```sh
python -m pip install --upgrade pip
```

Установите и проверьте запуск TensorFlow:
```sh
pip install tensorflow
python -c "import tensorflow as tf; print(tf.__version__)"
```

Примечание. Если выходит ошибка "Недопустимая инструкция (образ памяти сброшен на диск)", значит ваш процессор не поддерживает AVX/AVX2, стандартные версии TensorFlow не будут работать, так как они требуют эти инструкции.

Попробуйте удалить текущую и установить альтернативную версию:
```sh
pip uninstall tensorflow
pip install --no-cache-dir https://github.com/sld/Tensorflow-cpu_Docker-builder/releases/tag/v2.18.0/tensorflow_text-2.18.0-cp310-cp310-linux_x86_64.whl
```

Установите OpenCV:
```sh
pip install opencv-python
```

Установите библиотеки для работы с Dobot Magician:
- https://github.com/luismesas/pydobot
```sh
pip install pydobot==1.3.2
```

- https://github.com/sammydick22/pydobotplus
```sh
pip install pydobotplus==0.1.2
```

## Активация SSH на Linux:

Установите SSH Server:
```sh
sudo apt install openssh-server -y
```

Проверьте статус службы SSH:
```sh
sudo systemctl status ssh
```

Если служба не запущена, включите её:
```sh
sudo systemctl enable --now ssh
```

Узнайте IP-адрес устройства:
```sh
ip a
```
Нужно найти запись наподобие `inet 192.168.1.100/24`

Попробуйте подключиться:
```sh
ssh <имя пользователя>@<IP-адрес устройства>
```
