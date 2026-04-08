# src/parsers/docx_parser.py
import re
from datetime import datetime, date, time
from typing import List, Dict, Any
from io import BytesIO
from docx import Document

def parse_flight_docx(file_content: bytes) -> Dict[str, Any]:
    """
    Парсит DOCX файл с заявкой на выполнение полетов.
    Возвращает словарь с датой и списком рейсов.
    """
    doc = Document(BytesIO(file_content))
    
    result = {
        "departure_date": None,
        "weekday": None,
        "flights": []
    }
    
    date_pattern = re.compile(r'на\s+«(\d+)»\s+([а-я]+)\s+(\d{4})г\s+([а-я]+)', re.IGNORECASE)
    
    flight_pattern = re.compile(
        r'(\d+)\.\s+'                      # номер рейса
        r'([А-Яа-я0-9\-]+)\s+'             # тип вертолёта
        r'(\d+)\s+'                        # бортовой номер
        r'ГЗП\s+'
        r'(\d+)\s+'
        r'время вылета\s+'
        r'(\d{2}:\d{2})\s+'
        r'кол-во кресел\s+'
        r'(\d+)', re.IGNORECASE
    )
    
    route_pattern = re.compile(r'Маршрут:\s*(.+)', re.IGNORECASE)
    
    paragraphs = list(doc.paragraphs)
    i = 0
    
    while i < len(paragraphs):
        text = paragraphs[i].text.strip()
        
        # Поиск даты
        if not result["departure_date"]:
            date_match = date_pattern.search(text)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2).lower()
                year = int(date_match.group(3))
                
                # Преобразование названия месяца в номер
                month_map = {
                    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
                }
                month = month_map.get(month_str, 1)
                
                result["departure_date"] = date(year, month, day)
                result["weekday"] = date_match.group(4)
                i += 1
                continue
        
        # Поиск рейса
        flight_match = flight_pattern.search(text)
        if flight_match:
            flight_number = int(flight_match.group(1))
            aircraft_type = flight_match.group(2)
            tail_number = flight_match.group(3)
            gzp = flight_match.group(4)
            departure_time_str = flight_match.group(5)
            place_number = int(flight_match.group(6))
            
            # Парсим время
            departure_time = datetime.strptime(departure_time_str, "%H:%M").time()
            
            # Ищем маршрут в следующем параграфе
            route_str = ""
            if i + 1 < len(paragraphs):
                next_text = paragraphs[i + 1].text.strip()
                route_match = route_pattern.search(next_text)
                if route_match:
                    route_str = route_match.group(1).strip()
                    i += 1
            
            # Если маршрут не найден в следующем параграфе, ищем в текущем
            if not route_str:
                route_match = route_pattern.search(text)
                if route_match:
                    route_str = route_match.group(1).strip()
            
            result["flights"].append({
                "flight_number": flight_number,
                "aircraft_type": aircraft_type,
                "tail_number": tail_number,
                "gzp": gzp,
                "departure_time": departure_time,
                "place_number": place_number,
                "route": route_str
            })
        
        i += 1
    
    return result