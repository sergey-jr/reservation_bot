# restaurant reserve bot
Бот для резерва столиков в ресторане. Реализован на API Telegram
## Функционал
* Резерв столиков
* отмена (конкретного/всех) резерв(а/ов)
* Вывод списка бронирований
* регистрация (посредством передачи ПД)
## Стек
* python
    * python-telegram-bot
    * SQLAlchemy
* SQLite
## Запуск
```shell
docker build -t bot_daemon .
docker run -it -e TOKEN="YOUR_TOKEN" bot_daemon
```