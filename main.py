# main.py
# 🏓 PING-PONG ULTRA - Главная точка входа
# Запускайте игру через этот файл!

import subprocess
import sys
import os
import json

# --- Конфигурация ---
TITLE = "🏓 PING-PONG ULTRA 🏓"
VERSION = "1.0.0"

# --- Цвета для консоли ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_colored(text, color=Colors.WHITE):
    """Вывод цветного текста в консоль"""
    print(f"{color}{text}{Colors.RESET}")

def check_dependencies():
    """Проверка установленных зависимостей"""
    required = ['pygame', 'websockets', 'asyncio']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print_colored("⚠️  Отсутствуют необходимые библиотеки!", Colors.YELLOW)
        print_colored(f"Установите их командой:", Colors.YELLOW)
        print_colored(f"pip install {' '.join(missing)}", Colors.CYAN)
        print()
        return False
    return True

def check_assets():
    """Проверка наличия файлов игры"""
    required_files = [
        'config.py',
        'game.py',
        'server.py',
        'client.py',
        'menu.py',
        'sound_manager.py'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print_colored("⚠️  Отсутствуют файлы проекта!", Colors.YELLOW)
        for f in missing:
            print_colored(f"  - {f}", Colors.RED)
        return False
    return True

def check_sounds():
    """Проверка звуковых файлов"""
    sound_dir = 'assets/sounds'
    required_sounds = ['hit.wav', 'score.wav', 'click.wav', 'win.wav']
    
    if not os.path.exists(sound_dir):
        print_colored("⚠️  Папка assets/sounds не найдена!", Colors.YELLOW)
        return False
    
    missing = []
    for sound in required_sounds:
        path = os.path.join(sound_dir, sound)
        if not os.path.exists(path):
            missing.append(sound)
    
    if missing:
        print_colored(f"⚠️  Отсутствуют звуковые файлы: {missing}", Colors.YELLOW)
        return False
    
    return True

def display_header():
    """Отображение заголовка программы"""
    print()
    print_colored("=" * 50, Colors.CYAN)
    print_colored(f"{Colors.BOLD}{TITLE}{Colors.RESET}", Colors.CYAN)
    print_colored(f"{Colors.BOLD}Версия: {VERSION}{Colors.RESET}", Colors.CYAN)
    print_colored("=" * 50, Colors.CYAN)
    print()

def display_menu():
    """Отображение главного меню"""
    print_colored("Выберите режим игры:", Colors.WHITE)
    print()
    print_colored("  1️⃣  🎮 Одиночная игра (с ботом)", Colors.GREEN)
    print_colored("  2️⃣  🟢 Создать сервер (хост)", Colors.BLUE)
    print_colored("  3️⃣  🔵 Подключиться к серверу", Colors.CYAN)
    print_colored("  4️⃣  ⚙️  Настройки", Colors.YELLOW)
    print_colored("  5️⃣  ❌ Выйти", Colors.RED)
    print()

def load_settings():
    """Загрузка настроек из файла"""
    if os.path.exists('settings.json'):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "volume": 70,
        "difficulty": "Normal",
        "fullscreen": False,
        "player_name": "Player1",
        "sound_enabled": True
    }

def show_settings():
    """Отображение и редактирование настроек"""
    settings = load_settings()
    
    print()
    print_colored("=" * 50, Colors.CYAN)
    print_colored("⚙️  НАСТРОЙКИ", Colors.CYAN)
    print_colored("=" * 50, Colors.CYAN)
    print()
    print_colored(f"🔊 Громкость: {settings.get('volume', 70)}%", Colors.WHITE)
    print_colored(f"🎮 Сложность: {settings.get('difficulty', 'Normal')}", Colors.WHITE)
    print_colored(f"👤 Имя игрока: {settings.get('player_name', 'Player1')}", Colors.WHITE)
    print_colored(f"🔈 Звук: {'Вкл' if settings.get('sound_enabled', True) else 'Выкл'}", Colors.WHITE)
    print()
    
    while True:
        print_colored("Изменить:", Colors.YELLOW)
        print_colored("  1 - Громкость", Colors.WHITE)
        print_colored("  2 - Сложность", Colors.WHITE)
        print_colored("  3 - Имя игрока", Colors.WHITE)
        print_colored("  4 - Звук (Вкл/Выкл)", Colors.WHITE)
        print_colored("  0 - Назад", Colors.WHITE)
        print()
        
        choice = input("Ваш выбор: ").strip()
        
        if choice == "1":
            try:
                vol = int(input("Введите громкость (0-100): ").strip())
                settings['volume'] = max(0, min(100, vol))
                print_colored(f"✅ Громкость установлена: {settings['volume']}%", Colors.GREEN)
            except:
                print_colored("❌ Неверное значение!", Colors.RED)
        
        elif choice == "2":
            diffs = ["Easy", "Normal", "Hard", "Ultra"]
            current = settings.get('difficulty', 'Normal')
            idx = diffs.index(current) if current in diffs else 0
            new_idx = (idx + 1) % len(diffs)
            settings['difficulty'] = diffs[new_idx]
            print_colored(f"✅ Сложность: {settings['difficulty']}", Colors.GREEN)
        
        elif choice == "3":
            name = input("Введите имя игрока: ").strip()
            if name:
                settings['player_name'] = name
                print_colored(f"✅ Имя: {settings['player_name']}", Colors.GREEN)
        
        elif choice == "4":
            settings['sound_enabled'] = not settings.get('sound_enabled', True)
            status = "Вкл" if settings['sound_enabled'] else "Выкл"
            print_colored(f"✅ Звук: {status}", Colors.GREEN)
        
        elif choice == "0":
            # Сохранение настроек
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            print_colored("💾 Настройки сохранены!", Colors.GREEN)
            break
        else:
            print_colored("❌ Неверный выбор!", Colors.RED)
        
        print()

def run_game(mode):
    """Запуск игрового режима"""
    try:
        if mode == 1:
            print_colored("\n🎮 Запуск одиночной игры...", Colors.GREEN)
            subprocess.run([sys.executable, "game.py"])
        
        elif mode == 2:
            print_colored("\n🟢 Запуск сервера...", Colors.BLUE)
            print_colored("📡 Ожидаем подключения игрока...", Colors.CYAN)
            subprocess.run([sys.executable, "server.py"])
        
        elif mode == 3:
            print_colored("\n🔵 Запуск клиента...", Colors.CYAN)
            print_colored("💡 Вам понадобится IP-адрес сервера", Colors.YELLOW)
            subprocess.run([sys.executable, "client.py"])
    
    except FileNotFoundError:
        print_colored("❌ Ошибка: Файл игры не найден!", Colors.RED)
    except Exception as e:
        print_colored(f"❌ Ошибка запуска: {e}", Colors.RED)

def main():
    """Главная функция"""
    # Проверка зависимостей
    if not check_dependencies():
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверка файлов
    if not check_assets():
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверка звуков (не критично)
    check_sounds()
    
    # Главный цикл
    while True:
        display_header()
        display_menu()
        
        choice = input("Ваш выбор: ").strip()
        
        if choice == "1":
            run_game(1)
        
        elif choice == "2":
            run_game(2)
        
        elif choice == "3":
            run_game(3)
        
        elif choice == "4":
            show_settings()
        
        elif choice == "5":
            print()
            print_colored("👋 Спасибо за игру!", Colors.CYAN)
            print_colored("До встречи в Ping-Pong Ultra!", Colors.CYAN)
            print()
            break
        
        else:
            print()
            print_colored("❌ Неверный выбор! Попробуйте снова.", Colors.RED)
            print()
            input("Нажмите Enter для продолжения...")
        
        print()

# --- Точка входа ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_colored("👋 Игра прервана пользователем", Colors.YELLOW)
    except Exception as e:
        print()
        print_colored(f"❌ Критическая ошибка: {e}", Colors.RED)
        input("Нажмите Enter для выхода...")
