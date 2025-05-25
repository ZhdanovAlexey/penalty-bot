from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
import random

from services.sheets import GoogleSheetsService
from services.calculator import PenaltyCalculator
from services.database import db
from utils.validators import validate_amount, validate_date

# Определение ID канала, на который должны быть подписаны пользователи
# Убираем "-100" в начале, так как это префикс Telegram
CHANNEL_ID = -1002666468146
# ID канала в формате для создания ссылки
# Для приватных каналов нужно использовать invite-ссылку
CHANNEL_LINK = "https://t.me/sviridov_mikhail_Lawyer"

# ID администраторов бота, которые могут использовать admin команды
ADMIN_IDS = [862754324, 1698240710]  # Замените на реальные ID администраторов

# Различные варианты сообщений для неподписанных пользователей
SUBSCRIPTION_MESSAGES = [
    "⚠️ Вы всё еще не подписаны на наш канал.\n\n1️⃣ Нажмите кнопку «Подписаться на канал»\n2️⃣ После подписки нажмите «Проверить подписку»",
    "📢 Для использования бота необходимо подписаться на канал.\n\nПожалуйста, нажмите кнопку «Подписаться на канал» и затем «Проверить подписку»",
    "❗ Подписка на канал обязательна для использования бота.\n\nПодпишитесь на канал и нажмите «Проверить подписку»",
    "🔔 Напоминаем, что для доступа к функциям бота нужно подписаться на канал.\n\nНажмите «Подписаться на канал» и затем «Проверить подписку»"
]

# Состояние для ввода ID пользователя для ручного добавления подписки
class AdminForm(StatesGroup):
    add_user_id = State()

# Define states for the conversation
class PenaltyForm(StatesGroup):
    check_subscription = State()
    contract_amount = State()
    deadline_date = State()
    calculation_date = State()
    participant_type = State()
    is_unique = State()
    

# Initialize router
router = Router()


# Function to check channel subscription
async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """
    Проверка подписки пользователя на канал
    
    Сначала проверяем в базе данных, и только если там нет - 
    пытаемся проверить через API Telegram
    """
    # Debug logging
    print(f"Checking subscription for user {user_id}")
    
    # Проверяем в базе данных
    db_status = db.is_user_subscribed(user_id)
    print(f"DB subscription status: {db_status}")
    
    if db_status:
        return True
        
    # Проверяем через API Telegram
    try:
        print(f"Checking via Telegram API, channel_id={CHANNEL_ID}")
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        print(f"Member status: {member.status}")
        
        # Проверка, что пользователь не покинул канал (left) и не был кикнут (kicked)
        is_subscribed_via_api = member.status not in ['left', 'kicked']
        print(f"API subscription result: {is_subscribed_via_api}")
        
        # Если пользователь подписан, сохраняем в БД
        if is_subscribed_via_api:
            db.add_subscribed_user(
                user_id=user_id,
                is_subscribed=True
            )
        
        return is_subscribed_via_api
        
    except TelegramAPIError as e:
        # Вероятно, бот не является администратором канала или неверный ID канала
        print(f"Telegram API error: {e}")
        
        # Временное решение: автоматически добавляем пользователя как подписанного в случае ошибки
        print(f"Auto-approving user {user_id} due to channel configuration error")
        db.add_subscribed_user(
            user_id=user_id,
            is_subscribed=True
        )
        return True


# Admin command to manually add a user as subscribed
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    # Сбрасываем любое предыдущее состояние
    await state.clear()
    
    if message.from_user.id not in ADMIN_IDS:
        # Если пользователь не админ, игнорируем команду
        return
    
    commands_info = (
        "🔐 <b>Административные команды:</b>\n\n"
        "/adduser - Добавить пользователя как подписанного по ID\n"
        "/stats - Получить статистику использования бота"
    )
    
    await message.answer(commands_info, parse_mode="HTML")


# Admin command to add a user as subscribed
@router.message(Command("adduser"))
async def cmd_add_user(message: Message, state: FSMContext):
    # Сбрасываем любое предыдущее состояние
    await state.clear()
    
    if message.from_user.id not in ADMIN_IDS:
        # Если пользователь не админ, игнорируем команду
        return
    
    await message.answer(
        "Введите ID пользователя, которого нужно добавить как подписанного:\n\n"
        "💡 Для отмены используйте команду /cancel"
    )
    await state.set_state(AdminForm.add_user_id)


# Cancel command handler
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("❌ Нет активных действий для отмены.")
        return
    
    await state.clear()
    await message.answer("✅ Текущее действие отменено.")


# Handler for user ID input
@router.message(AdminForm.add_user_id)
async def process_add_user_id(message: Message, state: FSMContext):
    # Проверяем, не является ли это командой
    if message.text.startswith('/'):
        await message.answer("❌ Ожидается ID пользователя, а не команда. Для отмены используйте /cancel")
        return
    
    # Validate user ID
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID пользователя. Введите числовой ID или /cancel для отмены:")
        return
    
    # Add user to database
    success = db.add_subscribed_user(user_id)
    
    if success:
        await message.answer(f"✅ Пользователь с ID {user_id} успешно добавлен как подписанный.")
    else:
        await message.answer(f"❌ Ошибка при добавлении пользователя с ID {user_id}.")
    
    await state.clear()


# Admin command to get statistics
@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext):
    # Сбрасываем любое предыдущее состояние
    await state.clear()
    
    if message.from_user.id not in ADMIN_IDS:
        # Если пользователь не админ, игнорируем команду
        return
    
    # Получаем статистику из базы данных
    stats = db.get_statistics()
    
    # Форматируем данные для отображения
    avg_penalty = round(stats.get("avg_penalty", 0), 2)
    avg_contract = round(stats.get("avg_contract_amount", 0), 2)
    
    stats_message = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
        f"✅ Подписанных пользователей: {stats.get('subscribed_users', 0)}\n"
        f"🧮 Всего расчетов: {stats.get('total_calculations', 0)}\n\n"
        f"💰 Средняя сумма ДДУ: {avg_contract:,.2f} руб.\n"
        f"💸 Средняя сумма неустойки: {avg_penalty:,.2f} руб.\n\n"
        f"👤 Расчеты для физлиц: {stats.get('individual_calculations', 0)}\n"
        f"🏢 Расчеты для юрлиц: {stats.get('legal_calculations', 0)}\n"
        f"🏗 Расчеты для уникальных объектов: {stats.get('unique_objects_calculations', 0)}"
    )
    
    await message.answer(stats_message, parse_mode="HTML")


# Help command handler
@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    # Сбрасываем любое предыдущее состояние
    await state.clear()
    
    help_text = (
        "❓ <b>Помощь по использованию бота</b>\n\n"
        "🚀 <b>/start</b> - Начать новый расчет неустойки по ДДУ\n"
        "🔄 <b>/reset</b> - Сбросить текущий расчет и начать заново\n"
        "❓ <b>/help</b> - Показать это сообщение с помощью\n"
        "ℹ️ <b>/about</b> - Информация о боте и расчетах\n\n"
        
        "📋 <b>Как пользоваться ботом:</b>\n"
        "1️⃣ Подпишитесь на наш канал (обязательно)\n"
        "2️⃣ Введите команду /start\n"
        "3️⃣ Следуйте инструкциям бота:\n"
        "   • Укажите сумму по ДДУ\n"
        "   • Введите крайнюю дату передачи объекта\n"
        "   • Введите дату для расчета неустойки\n"
        "   • Выберите тип участника (ФЛ/ЮЛ)\n"
        "   • Укажите, является ли объект уникальным\n"
        "4️⃣ Получите результат расчета\n\n"
        
        "💡 <b>Полезные советы:</b>\n"
        "• Даты вводите в формате ДД.ММ.ГГГГ (например: 15.03.2025)\n"
        "• Сумму можно вводить с пробелами (например: 3 500 000)\n"
        "• Дата расчета должна быть позже крайней даты передачи\n"
        "• Если возникли проблемы, используйте /reset и начните заново\n\n"
        
        "📞 <b>Поддержка:</b>\n"
        "Если у вас возникли вопросы, обратитесь к администратору канала."
    )
    
    await message.answer(help_text, parse_mode="HTML")


# About command handler
@router.message(Command("about"))
async def cmd_about(message: Message, state: FSMContext):
    # Сбрасываем любое предыдущее состояние
    await state.clear()
    
    about_text = (
        "ℹ️ <b>О боте-калькуляторе неустойки по ДДУ</b>\n\n"
        
        "🎯 <b>Назначение:</b>\n"
        "Бот рассчитывает неустойку за просрочку передачи объекта долевого строительства "
        "в соответствии с действующим законодательством РФ.\n\n"
        
        "⚖️ <b>Правовая основа:</b>\n"
        "• Федеральный закон № 214-ФЗ \"Об участии в долевом строительстве\"\n"
        "• Ставки рефинансирования Центрального Банка РФ\n"
        "• Учет периодов моратория на начисление неустойки\n\n"
        
        "🧮 <b>Формулы расчета:</b>\n"
        "• <b>Физлица (обычные объекты):</b> 1/150 × ставка ЦБ × сумма ДДУ × дни\n"
        "• <b>Юрлица (обычные объекты):</b> 1/300 × ставка ЦБ × сумма ДДУ × дни\n"
        "• <b>Уникальные объекты:</b> 1/300 × ставка ЦБ × сумма ДДУ × дни (макс. 5%)\n\n"
        
        "📊 <b>Источники данных:</b>\n"
        "• Ставки рефинансирования загружаются из актуальной базы данных\n"
        "• Учитываются все периоды моратория\n"
        "• Данные обновляются регулярно\n\n"
        
        "⚠️ <b>Важно:</b>\n"
        "Результат расчета носит информационный характер. "
        "Для юридически значимых расчетов рекомендуется консультация с юристом.\n\n"
        
        "🔄 <b>Версия:</b> 2.0\n"
        "📅 <b>Последнее обновление:</b> Январь 2025"
    )
    
    await message.answer(about_text, parse_mode="HTML")


# Start command handler
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    # Сохраняем информацию о пользователе, даже если он не подписан
    db.add_subscribed_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
        is_subscribed=False  # Будет обновлено на True после проверки подписки
    )
    
    # Проверяем подписку на канал
    is_user_subscribed = await is_subscribed(bot, message.from_user.id)
    
    if not is_user_subscribed:
        # Создаем клавиатуру с кнопками
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Подписаться на канал", url=CHANNEL_LINK)
        builder.button(text="🔄 Проверить подписку", callback_data="check_subscription")
        
        await message.answer(
            "👋 Добро пожаловать в калькулятор неустойки по ДДУ!\n\n"
            "⚠️ Для использования бота необходимо подписаться на наш канал.\n\n"
            "1️⃣ Нажмите кнопку «Подписаться на канал»\n"
            "2️⃣ После подписки нажмите «Проверить подписку»",
            reply_markup=builder.as_markup()
        )
        
        await state.set_state(PenaltyForm.check_subscription)
        return
    
    # Если пользователь уже подписан, обновляем статус в базе
    db.add_subscribed_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
        is_subscribed=True
    )
    
    # Начинаем работу с ботом
    await message.answer(
        "👋 Добро пожаловать в калькулятор неустойки по ДДУ!\n\n"
        "Введите стоимость объекта по ДДУ (в рублях). Например: 3500000"
    )
    
    # Добавляем клавиатуру с быстрыми действиями
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Помощь", callback_data="quick_help")
    builder.button(text="ℹ️ О боте", callback_data="quick_about")
    builder.adjust(2)  # Размещаем кнопки в ряд
    
    await message.answer(
        "💡 <b>Быстрые действия:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(PenaltyForm.contract_amount)


# Callback для проверки подписки или ручной маркировки как подписанного
@router.callback_query(PenaltyForm.check_subscription, F.data == "check_subscription")
async def process_check_subscription(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Проверяем подписку на канал
    is_user_subscribed = await is_subscribed(bot, callback.from_user.id)
    
    if not is_user_subscribed:
        # В случае ошибок с проверкой, пометим пользователя как подписанного принудительно
        # но только если он уже нажимал на кнопку проверки подписки несколько раз
        user_data = await state.get_data()
        retry_count = user_data.get('subscription_retry_count', 0) + 1
        await state.update_data(subscription_retry_count=retry_count)
        
        print(f"Subscription check retry count: {retry_count}")
        
        # После 3 попыток, просто помечаем как подписанного
        if retry_count >= 3:
            print(f"Forcing subscription for user {callback.from_user.id} after {retry_count} retries")
            db.add_subscribed_user(
                user_id=callback.from_user.id,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
                username=callback.from_user.username,
                is_subscribed=True
            )
            
            try:
                await callback.message.edit_text(
                    "✅ Статус подписки подтвержден! Теперь вы можете использовать бота.\n\n"
                    "Введите стоимость объекта по ДДУ (в рублях). Например: 3500000"
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    await callback.message.answer(
                        "✅ Статус подписки подтвержден! Теперь вы можете использовать бота.\n\n"
                        "Введите стоимость объекта по ДДУ (в рублях). Например: 3500000"
                    )
                else:
                    raise
            
            await state.set_state(PenaltyForm.contract_amount)
            return
        
        # Выбираем случайное сообщение для неподписанных пользователей
        random_message = random.choice(SUBSCRIPTION_MESSAGES)
        
        # Создаем клавиатуру с кнопками
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Подписаться на канал", url=CHANNEL_LINK)
        builder.button(text="🔄 Проверить подписку", callback_data="check_subscription")
        
        try:
            await callback.message.edit_text(random_message, reply_markup=builder.as_markup())
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # Если сообщение не изменилось, показываем уведомление
                await callback.answer("⚠️ Вы еще не подписались на канал", show_alert=True)
            else:
                raise
        return
    
    # Пользователь подписан, сохраняем информацию о нем
    db.add_subscribed_user(
        user_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username
    )
    
    # Продолжаем работу
    try:
        await callback.message.edit_text(
            "✅ Спасибо за подписку! Теперь вы можете использовать бота.\n\n"
            "Введите стоимость объекта по ДДУ (в рублях). Например: 3500000"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Если не удалось отредактировать сообщение, просто отправляем новое
            await callback.message.answer(
                "✅ Спасибо за подписку! Теперь вы можете использовать бота.\n\n"
                "Введите стоимость объекта по ДДУ (в рублях). Например: 3500000"
            )
        else:
            raise
    
    await state.set_state(PenaltyForm.contract_amount)


# Reset command handler
@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext, bot: Bot):
    # Проверяем и сохраняем информацию о пользователе
    is_user_subscribed = await is_subscribed(bot, message.from_user.id)
    
    # Обновляем информацию в базе данных
    db.add_subscribed_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
        is_subscribed=is_user_subscribed
    )
    
    if not is_user_subscribed:
        # Создаем клавиатуру с кнопками
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Подписаться на канал", url=CHANNEL_LINK)
        builder.button(text="🔄 Проверить подписку", callback_data="check_subscription")
        
        await message.answer(
            "⚠️ Для использования бота необходимо подписаться на наш канал.\n\n"
            "1️⃣ Нажмите кнопку «Подписаться на канал»\n"
            "2️⃣ После подписки нажмите «Проверить подписку»",
            reply_markup=builder.as_markup()
        )
        
        await state.set_state(PenaltyForm.check_subscription)
        return

    await state.clear()
    
    await message.answer(
        "🔄 Расчет сброшен. Чтобы начать заново, используйте /start"
    )


# Contract amount handler
@router.message(PenaltyForm.contract_amount)
async def process_contract_amount(message: Message, state: FSMContext):
    # Проверяем, не является ли это командой
    if message.text.startswith('/'):
        await message.answer("❌ Ожидается сумма по ДДУ, а не команда. Для отмены используйте /cancel")
        return
    
    # Validate input
    is_valid, amount, error = validate_amount(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error}. Пожалуйста, введите корректную сумму.")
        return
    
    # Save to state
    await state.update_data(contract_amount=amount)
    
    await message.answer(
        "✅ Сумма принята.\n\n"
        "Теперь введите крайнюю дату передачи объекта по ДДУ в формате ДД.ММ.ГГГГ.\n"
        "Например: 07.02.2025"
    )
    
    await state.set_state(PenaltyForm.deadline_date)


# Deadline date handler
@router.message(PenaltyForm.deadline_date)
async def process_deadline_date(message: Message, state: FSMContext):
    # Проверяем, не является ли это командой
    if message.text.startswith('/'):
        await message.answer("❌ Ожидается дата передачи объекта, а не команда. Для отмены используйте /cancel")
        return
    
    # Validate input
    is_valid, date_obj, error = validate_date(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error}. Пожалуйста, введите корректную дату.")
        return
    
    # Save to state
    await state.update_data(deadline_date=date_obj, deadline_date_str=message.text)
    
    await message.answer(
        "✅ Дата принята.\n\n"
        "Теперь введите дату для расчета неустойки в формате ДД.ММ.ГГГГ.\n"
        "Например: 20.05.2025"
    )
    
    await state.set_state(PenaltyForm.calculation_date)


# Calculation date handler
@router.message(PenaltyForm.calculation_date)
async def process_calculation_date(message: Message, state: FSMContext):
    # Проверяем, не является ли это командой
    if message.text.startswith('/'):
        await message.answer("❌ Ожидается дата расчета неустойки, а не команда. Для отмены используйте /cancel")
        return
    
    # Get deadline date from state
    user_data = await state.get_data()
    deadline_date_str = user_data.get("deadline_date_str")
    
    # Validate input
    is_valid, date_obj, error = validate_date(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error}. Пожалуйста, введите корректную дату.")
        return
    
    # Check that calculation date is after deadline date
    deadline_date = user_data.get("deadline_date")
    if date_obj <= deadline_date:
        await message.answer(
            "❌ Дата расчета должна быть позже крайней даты передачи объекта. "
            "Пожалуйста, введите корректную дату."
        )
        return
    
    # Save to state
    await state.update_data(calculation_date=date_obj, calculation_date_str=message.text)
    
    # Create keyboard for participant type
    builder = InlineKeyboardBuilder()
    builder.button(text="Физическое лицо", callback_data="participant:individual")
    builder.button(text="Юридическое лицо", callback_data="participant:legal")
    builder.adjust(1)  # Place buttons in a column
    
    await message.answer(
        "✅ Дата принята.\n\n"
        "Выберите тип участника долевого строительства:",
        reply_markup=builder.as_markup()
    )
    
    await state.set_state(PenaltyForm.participant_type)


# Participant type callback handler
@router.callback_query(PenaltyForm.participant_type, F.data.startswith("participant:"))
async def process_participant_type(callback: CallbackQuery, state: FSMContext):
    # Extract participant type from callback data
    participant_type = callback.data.split(":")[1]
    is_individual = participant_type == "individual"
    
    # Save to state
    await state.update_data(is_individual=is_individual)
    
    # Create keyboard for unique object
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data="unique:yes")
    builder.button(text="Нет", callback_data="unique:no")
    builder.adjust(2)  # Place buttons in a row
    
    await callback.message.edit_text(
        "✅ Тип участника принят.\n\n"
        "Является ли дом уникальным объектом?",
        reply_markup=builder.as_markup()
    )
    
    await state.set_state(PenaltyForm.is_unique)


# Unique object callback handler
@router.callback_query(PenaltyForm.is_unique, F.data.startswith("unique:"))
async def process_unique_object(callback: CallbackQuery, state: FSMContext):
    # Extract unique object status from callback data
    is_unique = callback.data.split(":")[1] == "yes"
    
    # Save to state
    await state.update_data(is_unique=is_unique)
    
    # Get all user data from state
    user_data = await state.get_data()
    
    await callback.message.edit_text(
        "✅ Данные приняты. Расчет неустойки...\n\n"
        "🔢 Параметры расчета:\n"
        f"💰 Сумма по ДДУ: {user_data['contract_amount']:,.2f} руб.\n"
        f"📅 Дата передачи по ДДУ: {user_data['deadline_date_str']}\n"
        f"📅 Дата расчета: {user_data['calculation_date_str']}\n"
        f"👤 Тип участника: {'Физическое лицо' if user_data['is_individual'] else 'Юридическое лицо'}\n"
        f"🏢 Уникальный объект: {'Да' if user_data['is_unique'] else 'Нет'}"
    )
    
    # Fetch data from Google Sheets
    try:
        sheets_service = GoogleSheetsService()
        rates_data = sheets_service.get_rates_and_moratoriums()
        
        # Calculate penalty
        calculator = PenaltyCalculator(rates_data)
        result = calculator.calculate_penalty(
            contract_amount=user_data["contract_amount"],
            deadline_date=user_data["deadline_date"],
            calculation_date=user_data["calculation_date"],
            is_individual=user_data["is_individual"],
            is_unique_object=user_data["is_unique"]
        )
        
        # Format message based on result
        if "message" in result:
            await callback.message.answer(result["message"])
            return
        
        # Format the result message
        participant_type = "Физлицо" if result["is_individual"] else "Юрлицо"
        object_type = "уникальный дом" if result["is_unique_object"] else "не уникальный дом"
        
        # Сохраняем результаты расчета в БД
        calculation_data = {**user_data, **result}
        db.save_calculation(callback.from_user.id, calculation_data)
        
        # Создаем клавиатуру для действий после расчета
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Новый расчет", callback_data="new_calculation")
        builder.button(text="❓ Помощь", callback_data="quick_help")
        builder.button(text="ℹ️ О боте", callback_data="quick_about")
        builder.adjust(1, 2)  # Первая кнопка отдельно, остальные в ряд
        
        await callback.message.answer(
            f"💰 Итоговая неустойка: {result['penalty_amount']:,.2f} руб.\n"
            f"📅 Просрочка: {result['delay_days']} дней "
            f"(из них {result['moratorium_days']} дней под мораторием)\n"
            f"💹 Ставка рефинансирования: {result['refinancing_rate']:.2f}% "
            f"(на дату {user_data['deadline_date_str']})\n"
            f"🔢 Условия: {participant_type}, {object_type}\n\n"
            f"Для нового расчета используйте /start\n"
            f"Для сброса текущего расчета используйте /reset",
            reply_markup=builder.as_markup()
        )
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        await callback.message.answer(
            f"❌ Произошла ошибка при расчете неустойки: {str(e)}\n"
            f"Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
        
        # Clear state
        await state.clear()


# Callback handlers for quick actions
@router.callback_query(F.data == "quick_help")
async def process_quick_help(callback: CallbackQuery):
    help_text = (
        "❓ <b>Краткая помощь</b>\n\n"
        "📋 <b>Порядок действий:</b>\n"
        "1️⃣ Введите сумму по ДДУ\n"
        "2️⃣ Укажите крайнюю дату передачи\n"
        "3️⃣ Введите дату расчета\n"
        "4️⃣ Выберите тип участника\n"
        "5️⃣ Укажите тип объекта\n\n"
        
        "💡 <b>Форматы ввода:</b>\n"
        "• Даты: ДД.ММ.ГГГГ (15.03.2025)\n"
        "• Суммы: можно с пробелами\n\n"
        
        "Для подробной помощи используйте /help"
    )
    
    await callback.answer()
    await callback.message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data == "quick_about")
async def process_quick_about(callback: CallbackQuery):
    about_text = (
        "ℹ️ <b>О калькуляторе неустойки</b>\n\n"
        "🎯 Рассчитывает неустойку по ДДУ согласно ФЗ-214\n\n"
        
        "🧮 <b>Формулы:</b>\n"
        "• ФЛ: 1/150 × ставка ЦБ × сумма × дни\n"
        "• ЮЛ: 1/300 × ставка ЦБ × сумма × дни\n"
        "• Уникальные: макс. 5% от суммы\n\n"
        
        "📊 Данные актуальны, учитывается мораторий\n\n"
        
        "Для подробной информации используйте /about"
    )
    
    await callback.answer()
    await callback.message.answer(about_text, parse_mode="HTML")


@router.callback_query(F.data == "new_calculation")
async def process_new_calculation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Очищаем состояние
    await state.clear()
    
    # Проверяем подписку
    is_user_subscribed = await is_subscribed(bot, callback.from_user.id)
    
    if not is_user_subscribed:
        # Создаем клавиатуру с кнопками
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Подписаться на канал", url=CHANNEL_LINK)
        builder.button(text="🔄 Проверить подписку", callback_data="check_subscription")
        
        await callback.message.answer(
            "⚠️ Для использования бота необходимо подписаться на наш канал.\n\n"
            "1️⃣ Нажмите кнопку «Подписаться на канал»\n"
            "2️⃣ После подписки нажмите «Проверить подписку»",
            reply_markup=builder.as_markup()
        )
        
        await state.set_state(PenaltyForm.check_subscription)
        return
    
    # Обновляем информацию о пользователе
    db.add_subscribed_user(
        user_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username,
        is_subscribed=True
    )
    
    await callback.answer()
    await callback.message.answer(
        "🚀 <b>Новый расчет неустойки по ДДУ</b>\n\n"
        "Введите стоимость объекта по ДДУ (в рублях). Например: 3500000",
        parse_mode="HTML"
    )
    
    # Добавляем клавиатуру с быстрыми действиями
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Помощь", callback_data="quick_help")
    builder.button(text="ℹ️ О боте", callback_data="quick_about")
    builder.adjust(2)
    
    await callback.message.answer(
        "💡 <b>Быстрые действия:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(PenaltyForm.contract_amount) 