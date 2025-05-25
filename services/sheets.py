import os
from datetime import datetime
from typing import List, Dict, Any, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

from config import GOOGLE_CREDS_FILE, SPREADSHEET_ID, SHEET_NAME


class GoogleSheetsService:
    """Service to interact with Google Sheets API"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._initialize_service()
        
    def _initialize_service(self):
        """Initialize the Google Sheets API service"""
        try:
            # Проверка существования файла
            if not os.path.exists(GOOGLE_CREDS_FILE):
                raise FileNotFoundError(f"Service account file not found: {GOOGLE_CREDS_FILE}. "
                                       f"Please create a service account and download the JSON key file.")
            
            # Проверка содержимого файла
            try:
                with open(GOOGLE_CREDS_FILE, 'r') as f:
                    creds_data = json.load(f)
                    
                # Проверяем наличие обязательных полей
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'token_uri']
                missing_fields = [field for field in required_fields if field not in creds_data]
                
                if missing_fields:
                    raise ValueError(f"Service account file is missing required fields: {', '.join(missing_fields)}")
                    
            except json.JSONDecodeError:
                raise ValueError(f"Service account file is not a valid JSON file: {GOOGLE_CREDS_FILE}")
            
            # Инициализация сервиса
            self.creds = service_account.Credentials.from_service_account_file(
                GOOGLE_CREDS_FILE, 
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            self.service = build("sheets", "v4", credentials=self.creds)
            
        except Exception as e:
            print(f"Error initializing Google Sheets service: {e}")
            
            # Добавляем инструкции по исправлению
            if isinstance(e, FileNotFoundError):
                print("\nРешение: Создайте сервисный аккаунт в Google Cloud Console и загрузите JSON файл в data/service_account.json")
                print("Подробные инструкции находятся в файле data/README.md")
            elif isinstance(e, ValueError) and "missing fields" in str(e):
                print("\nРешение: Файл сервисного аккаунта некорректен. Скачайте новый файл ключа сервисного аккаунта.")
                print("Подробные инструкции находятся в файле data/README.md")
            
            raise
    
    def get_rates_and_moratoriums(self) -> List[Dict[str, Any]]:
        """Get rates and moratorium data from the Google Sheet
        
        Returns:
            List of dictionaries containing:
            - date (datetime): Date
            - rate (float): Refinancing rate (as decimal)
            - moratorium (bool): Whether there's a moratorium that day
        """
        try:
            if not SPREADSHEET_ID:
                raise ValueError("SPREADSHEET_ID not set. Please check your .env file.")
                
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A2:C"  # Assuming headers are in row 1
            ).execute()
            
            values = result.get("values", [])
            
            if not values:
                print(f"No data found in spreadsheet. Make sure the spreadsheet contains data and your service account has access.")
                return []
            
            data = []
            for row in values:
                if len(row) >= 3:  # Ensure the row has all required data
                    try:
                        # Parse date from string (DD.MM.YYYY)
                        date_str = row[0]
                        date = datetime.strptime(date_str, "%d.%m.%Y").date()
                        
                        # Parse rate from percentage (e.g., "10%")
                        rate_str = row[1].replace('%', '').replace(',', '.').strip()
                        rate = float(rate_str) / 100
                        
                        # Parse moratorium (0 or 1)
                        moratorium = bool(int(row[2]))
                        
                        data.append({
                            "date": date,
                            "rate": rate,
                            "moratorium": moratorium
                        })
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing row {row}: {e}")
                        continue
            
            return data
        
        except Exception as e:
            print(f"Error fetching data from Google Sheets: {e}")
            
            if "access" in str(e).lower():
                print("\nРешение: Убедитесь, что вы предоставили доступ к таблице для сервисного аккаунта.")
                print(f"Email сервисного аккаунта можно найти в файле {GOOGLE_CREDS_FILE} в поле 'client_email'.")
            
            return [] 