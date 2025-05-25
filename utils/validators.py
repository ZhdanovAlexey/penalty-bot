from datetime import datetime
from typing import Union, Tuple, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


def validate_amount(amount_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate contract amount input
    
    Args:
        amount_str: String input from user
        
    Returns:
        Tuple of (is_valid, amount_float, error_message)
    """
    try:
        # Remove spaces and replace commas with dots
        cleaned_amount = amount_str.replace(" ", "").replace(",", ".")
        amount = float(cleaned_amount)
        
        if amount <= 0:
            return False, None, "Сумма должна быть положительным числом"
            
        return True, amount, None
    except ValueError:
        return False, None, "Введите корректное числовое значение"


def validate_date(date_str: str) -> Tuple[bool, Optional[datetime.date], Optional[str]]:
    """
    Validate date input in DD.MM.YYYY format
    
    Args:
        date_str: String input from user
        
    Returns:
        Tuple of (is_valid, date_object, error_message)
    """
    try:
        # Check format
        if len(date_str.split(".")) != 3:
            return False, None, "Дата должна быть в формате ДД.ММ.ГГГГ"
            
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        return True, date_obj, None
    except ValueError:
        return False, None, "Введите корректную дату в формате ДД.ММ.ГГГГ"


def validate_calculation_date(calc_date_str: str, deadline_date_str: str) -> Tuple[bool, Optional[datetime.date], Optional[str]]:
    """
    Validate calculation date in relation to deadline date
    
    Args:
        calc_date_str: String input for calculation date
        deadline_date_str: String input for deadline date
        
    Returns:
        Tuple of (is_valid, date_object, error_message)
    """
    valid, calc_date, error = validate_date(calc_date_str)
    if not valid:
        return False, None, error
        
    valid, deadline_date, error = validate_date(deadline_date_str)
    if not valid:
        return False, None, error
    
    # Calculation date should not be in the future
    today = datetime.now().date()
    if calc_date > today:
        return False, None, "Дата расчета не может быть в будущем"
        
    return True, calc_date, None


async def validate_channel(bot: Bot, channel_id: int) -> Tuple[bool, Optional[str]]:
    """
    Проверяет доступность канала и наличие прав у бота
    
    Args:
        bot: Экземпляр бота
        channel_id: ID канала для проверки
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        chat = await bot.get_chat(chat_id=channel_id)
        print(f"Channel info: {chat.title}, username: {chat.username}, type: {chat.type}")
        
        # Проверяем, является ли бот администратором
        bot_member = await bot.get_chat_member(chat_id=channel_id, user_id=bot.id)
        print(f"Bot status in channel: {bot_member.status}")
        
        if bot_member.status not in ['administrator', 'creator']:
            return False, f"Бот не является администратором канала {chat.title}"
        
        return True, None
    except TelegramAPIError as e:
        print(f"Error checking channel: {e}")
        return False, f"Ошибка при проверке канала: {e}" 