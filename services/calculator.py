from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Tuple

from config import DEFAULT_DIVISOR_FL, DEFAULT_DIVISOR_UL, UNIQUE_OBJECT_DIVISOR, UNIQUE_OBJECT_MAX_PERCENTAGE


class PenaltyCalculator:
    """Service for calculating penalty fees based on user data and rates"""
    
    def __init__(self, sheets_data: List[Dict[str, Any]]):
        """
        Initialize calculator with data from Google Sheets
        
        Args:
            sheets_data: List of dictionaries with date, rate, and moratorium info
        """
        self.data_by_date = {item["date"]: item for item in sheets_data}
    
    def _get_rate_for_date(self, target_date: date) -> float:
        """
        Get the refinancing rate for the given date.
        If no exact match found, find the closest previous date.
        
        Args:
            target_date: Date to get the rate for
            
        Returns:
            Refinancing rate as a decimal value (e.g., 0.075 for 7.5%)
        """
        # Check if we have data for this exact date
        if target_date in self.data_by_date:
            return self.data_by_date[target_date]["rate"]
        
        # If not, find the closest previous date
        current_date = target_date
        while current_date not in self.data_by_date and current_date > date(2000, 1, 1):  # Using a safe lower bound
            current_date -= timedelta(days=1)
            
        # If we still don't have data, return a default value or raise an error
        if current_date not in self.data_by_date:
            raise ValueError(f"Не удалось найти ставку рефинансирования для даты {target_date}")
            
        return self.data_by_date[current_date]["rate"]
    
    def calculate_penalty(
        self,
        contract_amount: float,
        deadline_date: date,
        calculation_date: date,
        is_individual: bool,
        is_unique_object: bool
    ) -> Dict[str, Any]:
        """
        Calculate penalty based on input parameters
        
        Args:
            contract_amount: Contract amount in rubles
            deadline_date: Deadline date from the contract
            calculation_date: Date for calculation
            is_individual: Whether the participant is an individual (True) or legal entity (False)
            is_unique_object: Whether the object is unique
            
        Returns:
            Dictionary with calculation results
        """
        # Calculate date range for the delay
        if calculation_date <= deadline_date:
            return {
                "penalty_amount": 0,
                "delay_days": 0,
                "moratorium_days": 0,
                "message": "Просрочка отсутствует. Дата расчета не наступила после крайней даты по ДДУ."
            }
        
        # Получаем ставку рефинансирования на дату deadline_date
        try:
            refinancing_rate = self._get_rate_for_date(deadline_date)
        except ValueError as e:
            return {
                "penalty_amount": 0,
                "delay_days": 0,
                "moratorium_days": 0,
                "message": str(e)
            }
            
        # Generate all dates in the delay period
        delay_period = []
        current_date = deadline_date + timedelta(days=1)  # Start from the day after deadline
        
        while current_date <= calculation_date:
            delay_period.append(current_date)
            current_date += timedelta(days=1)
        
        # Count days and calculate penalty
        total_days = len(delay_period)
        moratorium_days = 0
        effective_days = 0
        
        # Check for moratorium days
        for day in delay_period:
            # Get moratorium status for this day
            current_date = day
            
            # Try to get data for this exact date
            if current_date in self.data_by_date:
                day_data = self.data_by_date[current_date]
            else:
                # Find the closest previous date with data
                temp_date = current_date
                while temp_date not in self.data_by_date and temp_date > date(2000, 1, 1):
                    temp_date -= timedelta(days=1)
                
                # If we still don't have data, skip this day
                if temp_date not in self.data_by_date:
                    continue
                    
                day_data = self.data_by_date[temp_date]
            
            # Skip days with moratorium
            if day_data["moratorium"]:
                moratorium_days += 1
            else:
                effective_days += 1
        
        # Determine divisor based on client type and object uniqueness
        if is_unique_object:
            divisor = UNIQUE_OBJECT_DIVISOR
        else:
            divisor = DEFAULT_DIVISOR_FL if is_individual else DEFAULT_DIVISOR_UL
        
        # Calculate penalty using the fixed rate from deadline_date
        penalty_sum = (1 / divisor) * refinancing_rate * contract_amount * effective_days
        
        # For unique objects, check if penalty exceeds the maximum allowed
        if is_unique_object:
            max_penalty = contract_amount * UNIQUE_OBJECT_MAX_PERCENTAGE
            if penalty_sum > max_penalty:
                penalty_sum = max_penalty
        
        return {
            "penalty_amount": round(penalty_sum, 2),
            "delay_days": total_days,
            "moratorium_days": moratorium_days,
            "effective_days": effective_days,
            "is_individual": is_individual,
            "is_unique_object": is_unique_object,
            "refinancing_rate": refinancing_rate * 100  # Convert to percentage for display
        } 