# Browser chat with Redis

## Установка

### Общая инструкция

1) Установите Redis в вашу систему
2) Клонируйте этот репозиторий
3) Внутри, создайте venv:
```bash
python -m venv .venv
```
4) Активируйте
`source .venv/bin/activate`
5) Запустите
```bash
./run.sh
```

### Для Arch
```bash
git clone https://github.com/Neveix/python_live_chat
cd python_live_chat
sudo pacman -S redis
python -m venv .venv
source .venv/bin/activate
./run.sh
```

## Ключевые особенности

1) Возможность устанавливать никнейм
2) Возможность заходить в чужие комнаты или создавать свою
3) Возможность отправлять сообщения в чат
4) Возможность видеть чужие сообщения в чате
5) При перезапуске сервера сообщения, чаты, комнаты не удаляются.
6) Поддержка большого объёма сообщений в чатах.
