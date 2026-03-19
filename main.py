import asyncio
import numpy as np
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from live_thor_functions import generate_gif_from_random, generate_gif_from_start

BOT_TOKEN = "8676837793:AAEDdcPe7MsthIgoBJaVp4GvrXbVtZ-MhOI"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class GetField(StatesGroup):
    waiting_for_field = State()

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Команды:\n"
        "/get H W p — сгенерировать случайное поле H×W с вероятностью жизни p (0<p<1).\n"
        "/get n m — задать своё поле размером n×m. После команды отправьте поле построчно (только 0 и 1).\n"
        "/cancel — отменить ввод поля.\n"
        "/help — это сообщение."
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот, который строит гифку для игры 'Жизнь на торе'.\n"
                         "Используйте /help для списка команд.")

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного диалога.")
        return
    await state.clear()
    await message.answer("Ввод поля отменён.")

@dp.message(Command("get"))
async def cmd_get(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) == 4:
        try:
            H = int(args[1])
            W = int(args[2])
            p = float(args[3])
            if H <= 0 or W <= 0:
                await message.answer("H и W должны быть положительными.")
                return
            if not (0 < p < 1):
                await message.answer("p должно быть в интервале (0, 1).")
                return
        except ValueError:
            await message.answer("Ошибка в параметрах. Убедитесь, что H, W — целые, p — число.")
            return

        await message.answer("Генерирую GIF...")
        try:
            gif_bytes = generate_gif_from_random(H, W, p)
            await message.answer_animation(
                animation=BufferedInputFile(gif_bytes, filename="animation.gif")
            )
        except Exception as e:
            await message.answer(f"Ошибка при генерации: {e}")

    elif len(args) == 3:
        try:
            n = int(args[1])
            m = int(args[2])
            if n <= 0 or m <= 0:
                await message.answer("n и m должны быть положительными.")
                return
        except ValueError:
            await message.answer("Ошибка в параметрах. n и m должны быть целыми.")
            return

        await state.update_data(n=n, m=m)
        await state.set_state(GetField.waiting_for_field)
        await message.answer(
            f"Теперь отправьте поле размером {n}×{m}.\n"
            f"Каждая строка должна содержать ровно {m} символов (0 или 1).\n"
            f"Всего строк: {n}. Отправьте их одним сообщением."
        )

    else:
        await message.answer(
            "Неверный формат. Используйте:\n"
            "/get H W p — для случайного поля,\n"
            "/get n m — для своего поля."
        )

@dp.message(GetField.waiting_for_field)
async def process_field(message: Message, state: FSMContext):
    data = await state.get_data()
    n = data.get("n")
    m = data.get("m")
    if n is None or m is None:
        await message.answer("Ошибка: размеры не заданы. Начните сначала командой /get n m")
        await state.clear()
        return

    text = message.text.strip()
    lines = text.splitlines()
    if len(lines) != n:
        await message.answer(f"Ожидалось {n} строк, получено {len(lines)}. Попробуйте ещё раз.")
        return

    field_list = []
    for i, line in enumerate(lines):
        line = line.strip()
        if len(line) != m or any(c not in "01" for c in line):
            await message.answer(
                f"Строка {i+1} имеет длину {len(line)} или содержит недопустимые символы.\n"
                f"Ожидается {m} символов (только 0 и 1). Попробуйте ещё раз."
            )
            return
        field_list.append([c == "1" for c in line])

    field_np = np.array(field_list, dtype=bool)

    await message.answer("Генерирую GIF...")
    try:
        gif_bytes = generate_gif_from_start(field_np)
        await message.answer_animation(
            animation=BufferedInputFile(gif_bytes, filename="animation.gif")
        )
    except Exception as e:
        await message.answer(f"Ошибка при генерации: {e}")
    finally:
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())