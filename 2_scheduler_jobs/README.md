# Проектирование и реализация планировщика задач для выполнения поступающих задач

## Описание задания

**1. Реализация `Scheduler`.**

Условия и требования:
- Планировщик одновременно может выполнять до 10 задач (дефолтное значение, может быть изменено).
- Возможность добавить задачу в планировщик и запустить её в рамках ограничений планировщика и настроек, указанных в задаче.
- При штатном завершении работы планировщик сохраняет статус выполняемых и ожидающих задач.
- После рестарта восстанавливается последнее состояние и задачи продолжают выполняться.

**2. Реализация `Job`.**

Условия и требования:
- У задачи может быть указана длительность выполнения (опциональный параметр). Если параметр указан, то задача прекращает выполняться, если время выполнения превысило указанный параметр.
- У задачи может быть указано время запуска (опциональный параметр). Если параметр указан, то задача стартует в указанный временной период.
- У задачи может быть указан параметр количества рестартов (опциональный параметр). Если в ходе выполнения задачи произошёл сбой или задачи-зависимости не были выполнены, то задача будет перезапущена указанное количество раз. Если параметр не указан, то количество рестартов равно 0.
- У задачи может быть указаны зависимости — задача или задачи, от которых зависит её выполнение (опциональный параметр). Если параметр указан, то задача не может стартовать до момента, пока не будут завершены задачи-зависимости.


**3. Проверка реализации планировщика.**

Условия и требования:
- работа с файловой системой: создание, удаление, изменение директорий и файлов;
- работа с файлами: создание, чтение, запись;
- работа с сетью: обработка ссылок (GET-запросы) и анализ полученного результата;
- описать конвеер выполнения основной задачи минимум из 3 задач, зависящих друг от друга и выполняющихся последовательно друг за другом.


Схематично сервис представлен на [диаграмме](schema.png).
![image](schema.png)
