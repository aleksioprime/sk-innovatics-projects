# Программы для проекта с использованием Raspberry Pi и Dobot Magician

[Вернуться на главный README](../README.md)

Программы предназначены для запуска на ОС Linux Ubuntu

## Установка Linux

Скачайте и установите Linux Ubuntu Desktop Image на компьютер:

- Ubuntu 22.04.5 LTS (Jammy Jellyfish) ([ссылка](https://releases.ubuntu.com/22.04/))
- Ubuntu 24.04.1 (Noble Numbat) ([ссылка](https://releases.ubuntu.com/24.04/))

Инструкция по установке: [https://ubuntu.com/tutorials/install-ubuntu-desktop](https://ubuntu.com/tutorials/install-ubuntu-desktop)

## Подготовка окружения

Установите CURL:
```
sudo apt install curl
```

Установите GIT
```
sudo apt install git -y
```

### Установка и настройка PyEnv

Источник: [ссылка](https://github.com/pyenv/pyenv)

Установите pyenv
```
curl -fsSL https://pyenv.run | bash
```

Добавьте настройки в bashrc
```
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --patch)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
```

Альтернативный вариант.
Откройте файл для редактирования:
```
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
```
source ~/.bashrc
```

Проверьте версию pyenv:
```
pyenv --version
```

### Установка зависимостей для Linux

Установите пакеты среды:
```
sudo apt install -y libbz2-dev libnsurses-dev libffi-dev libreadline-dev libssl-dev libsqlite3-dev tk-dev liblzma-dev
```

Полный список зависимостей [источник](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)
```
sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl git \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

### Создание виртуальной среды окружения

Проверьте установленные плагины:
```
pyenv --version
pyenv virtualenvs
```

Установите версию Python:
```
pyenv install 3.9.21
```

Создайте виртуальное окружение:
```
pyenv virtualenv 3.9.21 trash
```

Активация виртуального окружения:
```
pyenv activate trash
```

Выход из виртуального окружения:
```
pyenv deactivate
```

### Установка необходимых библиотек

Обновите PIP:
```
python -m pip install --upgrade pip
```

Установите и проверьте запуск TensorFlow:
```
pip install tensorflow
python -c "import tensorflow as tf; print(tf.__version__)"
```

Примечание. Если выходит ошибка "Недопустимая инструкция (образ памяти сброшен на диск)",
значит ваш процессор не поддерживает AVX/AVX2, стандартные версии TensorFlow не будут работать,
так как они требуют эти инструкции.

Попробуйте удалить текущую и установить альтернативную версию:
```
pip uninstall tensorflow
pip install --no-cache-dir https://github.com/yaroslavvb/tensorflow-community-wheels/releases/download/v2.10.0/tensorflow-2.10.0-cp39-cp39-linux_x86_64.whl
```

Установите OpenCV:
```
pip install opencv-python
```

Установите библиотеки для работы с Dobot Magician:
```
pip install pydobot==1.3.2
pip install pyserial==3.4
```