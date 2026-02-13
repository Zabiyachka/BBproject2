"""
Алгоритми для Basketball AI Chat
=================================
1. Оптимізація чату - управління контекстом
2. Обробка баскетбольних даних - парсинг та аналітика
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import re


# ============================================================================
# 1️⃣ ОПТИМІЗАЦІЯ ЧАТУ - УПРАВЛІННЯ КОНТЕКСТОМ
# ============================================================================

class ChatContextManager:
    """
    Управління контекстом розмови для AI чату
    - зберігає історію повідомлень
    - обмежує токени
    - визначає релевантність
    """
    
    def __init__(self, max_messages: int = 10, max_tokens: int = 3000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.conversation_history = deque(maxlen=max_messages)
        
    def add_message(self, role: str, content: str):
        """Додає повідомлення до історії"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        self.conversation_history.append(message)
    
    def get_context_for_api(self) -> List[Dict[str, str]]:
        """
        Повертає контекст для OpenAI API
        Обрізає старі повідомлення якщо перевищено ліміт токенів
        """
        messages = []
        total_tokens = 0
        
        # Проходимо з кінця (найновіші повідомлення важливіші)
        for msg in reversed(self.conversation_history):
            # Приблизний підрахунок токенів (1 токен ≈ 4 символи)
            msg_tokens = len(msg["content"]) // 4
            
            if total_tokens + msg_tokens > self.max_tokens:
                break
                
            messages.insert(0, {
                "role": msg["role"],
                "content": msg["content"]
            })
            total_tokens += msg_tokens
        
        return messages
    
    def clear_old_messages(self, hours: int = 24):
        """Видаляє повідомлення старші за вказану кількість годин"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.conversation_history = deque(
            [msg for msg in self.conversation_history 
             if msg["timestamp"] > cutoff_time],
            maxlen=self.max_messages
        )
    
    def get_conversation_summary(self) -> str:
        """Створює короткий саммарі розмови"""
        if not self.conversation_history:
            return "Нова розмова"
        
        topics = self._extract_topics()
        return f"Обговорювали: {', '.join(topics)}"
    
    def _extract_topics(self) -> List[str]:
        """Витягує основні теми з розмови (простий варіант)"""
        basketball_keywords = {
            'гравець': 'гравці',
            'команда': 'команди',
            'матч': 'матчі',
            'статистика': 'статистику',
            'кидок': 'кидки',
            'очки': 'очки',
            'nba': 'NBA',
            'euroleague': 'Euroleague',
            'player': 'players',
            'team': 'teams',
            'game': 'games',
            'statistics': 'statistics',
            'points': 'points'
        }
        
        topics = set()
        for msg in self.conversation_history:
            content_lower = msg["content"].lower()
            for keyword, topic in basketball_keywords.items():
                if keyword in content_lower:
                    topics.add(topic)
        
        return list(topics)[:3]  # Топ-3 теми


class ResponseFilter:
    """
    Фільтрація та валідація відповідей AI
    - перевіряє релевантність
    - фільтрує небажаний контент
    - форматує відповіді
    """
    
    BASKETBALL_KEYWORDS = [
        'баскетбол', 'basketball', 'nba', 'гравець', 'player',
        'команда', 'team', 'матч', 'game', 'очки', 'points',
        'кидок', 'shot', 'euroleague', 'фінал', 'championship',
        'coach', 'тренер', 'training', 'тренування'
    ]
    
    @staticmethod
    def is_basketball_related(text: str) -> bool:
        """Перевіряє чи пов'язаний текст з баскетболом"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in ResponseFilter.BASKETBALL_KEYWORDS)
    
    @staticmethod
    def filter_response(response: str, user_question: str) -> Dict[str, Any]:
        """
        Фільтрує та валідує відповідь
        Повертає словник з результатом та метаданими
        """
        result = {
            "original": response,
            "filtered": response,
            "is_relevant": True,
            "confidence": 1.0,
            "warnings": []
        }
        
        # Перевірка релевантності
        if not ResponseFilter.is_basketball_related(user_question):
            result["is_relevant"] = False
            result["confidence"] = 0.3
            result["warnings"].append("Питання може не стосуватися баскетболу")
        
        # Видалення зайвих пробілів та форматування
        filtered = response.strip()
        filtered = re.sub(r'\n{3,}', '\n\n', filtered)  # Максимум 2 переноси підряд
        
        result["filtered"] = filtered
        
        return result
    
    @staticmethod
    def add_context_prefix(response: str, context_summary: str) -> str:
        """Додає контекст до відповіді якщо потрібно"""
        if context_summary and context_summary != "Нова розмова":
            return f"[Контекст: {context_summary}]\n\n{response}"
        return response


# ============================================================================
# 2️⃣ ОБРОБКА БАСКЕТБОЛЬНИХ ДАНИХ
# ============================================================================

class PlayerStats:
    """
    Клас для роботи зі статистикою гравців
    """
    
    def __init__(self, player_data: Dict[str, Any]):
        self.name = player_data.get('name', 'Unknown')
        self.points = player_data.get('points', 0)
        self.rebounds = player_data.get('rebounds', 0)
        self.assists = player_data.get('assists', 0)
        self.games_played = player_data.get('games_played', 1)
    
    def calculate_ppg(self) -> float:
        """Points Per Game"""
        return round(self.points / self.games_played, 1)
    
    def calculate_rpg(self) -> float:
        """Rebounds Per Game"""
        return round(self.rebounds / self.games_played, 1)
    
    def calculate_apg(self) -> float:
        """Assists Per Game"""
        return round(self.assists / self.games_played, 1)
    
    def calculate_efficiency(self) -> float:
        """
        Спрощений розрахунок ефективності гравця
        PER = (Points + Rebounds + Assists) / Games
        """
        total_stats = self.points + self.rebounds + self.assists
        return round(total_stats / self.games_played, 2)
    
    def get_summary(self) -> Dict[str, Any]:
        """Повертає повну статистику"""
        return {
            'name': self.name,
            'ppg': self.calculate_ppg(),
            'rpg': self.calculate_rpg(),
            'apg': self.calculate_apg(),
            'efficiency': self.calculate_efficiency()
        }


class PlayerComparator:
    """
    Порівняння гравців за статистикою
    """
    
    @staticmethod
    def compare_players(player1: PlayerStats, player2: PlayerStats) -> Dict[str, Any]:
        """
        Порівнює двох гравців
        Повертає детальне порівняння
        """
        stats1 = player1.get_summary()
        stats2 = player2.get_summary()
        
        comparison = {
            'player1': stats1,
            'player2': stats2,
            'winner': {},
            'differences': {}
        }
        
        # Порівнюємо кожну статистику
        for stat in ['ppg', 'rpg', 'apg', 'efficiency']:
            diff = stats1[stat] - stats2[stat]
            comparison['differences'][stat] = round(diff, 2)
            
            if diff > 0:
                comparison['winner'][stat] = player1.name
            elif diff < 0:
                comparison['winner'][stat] = player2.name
            else:
                comparison['winner'][stat] = 'Однаково'
        
        # Визначаємо загального переможця
        comparison['overall_winner'] = PlayerComparator._determine_overall_winner(
            stats1, stats2, player1.name, player2.name
        )
        
        return comparison
    
    @staticmethod
    def _determine_overall_winner(stats1: Dict, stats2: Dict, 
                                  name1: str, name2: str) -> str:
        """Визначає загального переможця за ефективністю"""
        if stats1['efficiency'] > stats2['efficiency']:
            return name1
        elif stats2['efficiency'] > stats1['efficiency']:
            return name2
        else:
            return 'Однаково'
    
    @staticmethod
    def rank_players(players: List[PlayerStats], by: str = 'efficiency') -> List[Dict]:
        """
        Ранжує гравців за вказаною статистикою
        by: 'ppg', 'rpg', 'apg', 'efficiency'
        """
        players_data = [p.get_summary() for p in players]
        
        # Сортуємо за вказаною метрикою
        sorted_players = sorted(
            players_data,
            key=lambda x: x.get(by, 0),
            reverse=True
        )
        
        # Додаємо ранг
        for i, player in enumerate(sorted_players, 1):
            player['rank'] = i
        
        return sorted_players


class GameAnalyzer:
    """
    Аналіз матчів та статистики команд
    """
    
    @staticmethod
    def calculate_team_stats(team_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Розраховує статистику команди
        team_data: {'players': [...], 'games': [...]}
        """
        players = team_data.get('players', [])
        
        total_points = sum(p.get('points', 0) for p in players)
        total_rebounds = sum(p.get('rebounds', 0) for p in players)
        total_assists = sum(p.get('assists', 0) for p in players)
        games_played = team_data.get('games_played', 1)
        
        return {
            'team_ppg': round(total_points / games_played, 1),
            'team_rpg': round(total_rebounds / games_played, 1),
            'team_apg': round(total_assists / games_played, 1),
            'total_players': len(players)
        }
    
    @staticmethod
    def predict_winner(team1_stats: Dict, team2_stats: Dict) -> Dict[str, Any]:
        """
        Простий алгоритм передбачення переможця
        На основі середньої кількості очок
        """
        team1_ppg = team1_stats.get('team_ppg', 0)
        team2_ppg = team2_stats.get('team_ppg', 0)
        
        diff = abs(team1_ppg - team2_ppg)
        
        if team1_ppg > team2_ppg:
            winner = 'Команда 1'
            probability = min(50 + (diff * 2), 90)  # Макс 90%
        elif team2_ppg > team1_ppg:
            winner = 'Команда 2'
            probability = min(50 + (diff * 2), 90)
        else:
            winner = 'Рівні шанси'
            probability = 50
        
        return {
            'predicted_winner': winner,
            'probability': round(probability, 1),
            'team1_ppg': team1_ppg,
            'team2_ppg': team2_ppg,
            'point_difference': round(diff, 1)
        }


class DataParser:
    """
    Парсинг баскетбольних даних з різних форматів
    """
    
    @staticmethod
    def parse_player_string(player_str: str) -> Dict[str, Any]:
        """
        Парсить рядок з даними гравця
        Формат: "LeBron James: 25.7 PPG, 7.8 RPG, 10.2 APG"
        """
        try:
            # Розділяємо імʼя та статистику
            parts = player_str.split(':')
            if len(parts) != 2:
                return None
            
            name = parts[0].strip()
            stats_str = parts[1].strip()
            
            # Парсимо статистику
            stats = {}
            stats_parts = stats_str.split(',')
            
            for stat in stats_parts:
                stat = stat.strip()
                if 'PPG' in stat:
                    stats['ppg'] = float(re.search(r'[\d.]+', stat).group())
                elif 'RPG' in stat:
                    stats['rpg'] = float(re.search(r'[\d.]+', stat).group())
                elif 'APG' in stat:
                    stats['apg'] = float(re.search(r'[\d.]+', stat).group())
            
            return {
                'name': name,
                **stats
            }
        except Exception as e:
            print(f"Помилка парсингу: {e}")
            return None
    
    @staticmethod
    def parse_game_score(score_str: str) -> Dict[str, Any]:
        """
        Парсить результат матчу
        Формат: "Lakers 105 - 98 Celtics"
        """
        try:
            # Шукаємо команди та рахунок
            match = re.search(r'(\w+)\s+(\d+)\s*-\s*(\d+)\s+(\w+)', score_str)
            
            if match:
                team1, score1, score2, team2 = match.groups()
                
                return {
                    'team1': team1,
                    'score1': int(score1),
                    'team2': team2,
                    'score2': int(score2),
                    'winner': team1 if int(score1) > int(score2) else team2,
                    'margin': abs(int(score1) - int(score2))
                }
        except Exception as e:
            print(f"Помилка парсингу рахунку: {e}")
        
        return None