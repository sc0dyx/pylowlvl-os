# Метод `aprint_auto`

Высокоуровневый метод для вывода ASCII-строк на экран.

## Как это работает

1. **Данные:** Пакует строку в ASCIIZ и кидает в секцию данных: `.str_id db "текст", 0`.
2. **Вызов:** Генерирует код: `mov si, .str_id` -> `call aprint16`.

## Стратегии `aprint16`

Зависят от `aprint16_method` при инициализации:

* **`bios_teletype`:** Вывод через `int 0x10` (`ah=0x0E`).
* **`bios_color`:** Цветной вывод через `int 0x10` (`ah=0x09`) со сдвигом курсора.
* **`direct`:** Прямая запись символа и цвета в MMIO по адресу `0xB800` через `es:di`.

## Пример использования

```python
from pylowlvl_os.x86_64.pyabstract import PyLowLvl

boot = PyLowLvl(aprint16_method="bios_teletype")
boot.init_enviroment16()

# Сам вызов
boot.aprint_auto("Hello world!")

boot.stoooop()

```
