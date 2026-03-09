# menu.py
# 🎛️ Система меню для Ping-Pong Ultra

import pygame
import json
import os
from config import *

# ─────────────────────────────────────────────────────────────────────────────
# КЛАСС КНОПКИ
# ─────────────────────────────────────────────────────────────────────────────
class Button:
    """
    Интерактивная кнопка с эффектом наведения и анимацией.
    """
    def __init__(self, x, y, width, height, text, callback, color=COLOR_ACCENT):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.hover_color = COLOR_ACCENT_HOVER
        self.current_color = self.base_color
        self.hovered = False
        self.font = pygame.font.Font(None, 36)
        self.visible = True

    def draw(self, screen):
        """Отрисовка кнопки"""
        if not self.visible:
            return

        # Обновление цвета при наведении
        self.current_color = self.hover_color if self.hovered else self.base_color

        # Рисуем кнопку с закругленными углами
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2, border_radius=10)

        # Рендер текста
        text_surf = self.font.render(self.text, True, COLOR_BG)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        """Проверка наведения мыши"""
        if self.visible:
            self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        """Обработка нажатия"""
        if self.visible and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                return True
        return False

    def set_text(self, new_text):
        """Обновление текста кнопки"""
        self.text = new_text


# ─────────────────────────────────────────────────────────────────────────────
# КЛАСС ПОЛЯ ВВОДА
# ─────────────────────────────────────────────────────────────────────────────
class InputBox:
    """
    Поле для ввода текста (используется для IP адреса).
    """
    def __init__(self, x, y, width, height, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.font = pygame.font.Font(None, 36)
        self.color_inactive = COLOR_TEXT
        self.color_active = COLOR_ACCENT
        self.blink_timer = 0
        self.show_cursor = True

    def draw(self, screen):
        """Отрисовка поля ввода"""
        # Рамка
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, color, self.rect, 2)

        # Текст
        display_text = self.text if self.text else self.placeholder
        text_color = COLOR_TEXT if self.text else (100, 100, 100)
        text_surf = self.font.render(display_text, True, text_color)
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 5))

        # Курсор
        if self.active and self.show_cursor:
            cursor_x = self.rect.x + 10 + text_surf.get_width()
            pygame.draw.line(screen, COLOR_TEXT, (cursor_x, self.rect.y + 5), 
                           (cursor_x, self.rect.y + 30), 2)

    def handle_event(self, event):
        """Обработка ввода текста"""
        # Клик мыши для активации
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.show_cursor = True

        # Ввод клавиш
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            else:
                # Ограничение длины и допустимые символы (для IP)
                if len(self.text) < 15:
                    char = event.unicode
                    if char.isdigit() or char == '.':
                        self.text += char
        
        return None

    def update_cursor(self, dt):
        """Анимация мигания курсора"""
        self.blink_timer += dt
        if self.blink_timer > 500:  # 500 мс
            self.show_cursor = not self.show_cursor
            self.blink_timer = 0

    def clear(self):
        """Очистка поля"""
        self.text = ""
        self.active = False

    def get_text(self):
        """Получение текста"""
        return self.text


# ─────────────────────────────────────────────────────────────────────────────
# КЛАСС МЕНЮ
# ─────────────────────────────────────────────────────────────────────────────
class Menu:
    """
    Главная система меню игры.
    Управляет состояниями: MAIN, ONLINE, CONNECTING, SETTINGS
    """
    def __init__(self, screen, sound_manager=None):
        self.screen = screen
        self.sound_manager = sound_manager
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 74)
        self.font_small = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()
        
        # Состояния меню
        self.state = "MAIN"  # MAIN, ONLINE, CONNECTING, SETTINGS
        self.running = True
        self.result = None  # Возвращаемое значение выбора
        
        # Настройки
        self.settings = self.load_settings()
        
        # Создание кнопок
        self.create_main_menu_buttons()
        self.create_online_buttons()
        self.create_settings_buttons()
        
        # Поле ввода IP
        self.ip_input = InputBox(SCREEN_WIDTH // 2 - 150, 350, 300, 40, "192.168.X.X")

    # ─────────────────────────────────────────────────────────────────────────
    # ЗАГРУЗКА И СОХРАНЕНИЕ
    # ─────────────────────────────────────────────────────────────────────────
    def load_settings(self):
        """Загрузка настроек из JSON файла"""
        default_settings = {
            "volume": 70,
            "difficulty": "Normal",
            "fullscreen": False,
            "player_name": "Player1",
            "sound_enabled": True
        }
        
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Объединяем с дефолтными (на случай обновлений структуры)
                    default_settings.update(loaded)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки настроек: {e}")
        
        return default_settings

    def save_settings(self):
        """Сохранение настроек в JSON файл"""
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения настроек: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # СОЗДАНИЕ КНОПОК
    # ─────────────────────────────────────────────────────────────────────────
    def create_main_menu_buttons(self):
        """Создание кнопок главного меню"""
        cx = SCREEN_WIDTH // 2
        self.btn_play_bot = Button(cx - 120, 250, 240, 50, "🎮 ИГРА С БОТОМ", self.play_bot)
        self.btn_play_online = Button(cx - 120, 320, 240, 50, "🌐 ОНЛАЙН ИГРА", self.play_online)
        self.btn_settings = Button(cx - 120, 390, 240, 50, "⚙️ НАСТРОЙКИ", self.open_settings)
        self.btn_exit = Button(cx - 120, 460, 240, 50, "❌ ВЫЙТИ", self.exit_game)
        self.main_buttons = [self.btn_play_bot, self.btn_play_online, self.btn_settings, self.btn_exit]

    def create_online_buttons(self):
        """Создание кнопок онлайн меню"""
        cx = SCREEN_WIDTH // 2
        self.btn_host = Button(cx - 120, 250, 240, 50, "🟢 СОЗДАТЬ ИГРУ", self.host_game)
        self.btn_join = Button(cx - 120, 320, 240, 50, "🔵 ПОДКЛЮЧИТЬСЯ", self.join_game)
        self.btn_back_online = Button(cx - 120, 500, 240, 50, "⬅️ НАЗАД", self.back_to_main)
        self.online_buttons = [self.btn_host, self.btn_join, self.btn_back_online]

    def create_settings_buttons(self):
        """Создание кнопок меню настроек"""
        cx = SCREEN_WIDTH // 2
        self.btn_vol_up = Button(cx - 150, 300, 60, 40, "+", self.volume_up)
        self.btn_vol_down = Button(cx + 90, 300, 60, 40, "-", self.volume_down)
        self.btn_diff = Button(cx - 120, 370, 240, 50, 
                              f"Сложность: {self.settings['difficulty']}", 
                              self.toggle_difficulty)
        self.btn_back_set = Button(cx - 120, 500, 240, 50, "⬅️ НАЗАД", self.back_to_main)
        self.settings_buttons = [self.btn_vol_up, self.btn_vol_down, self.btn_diff, self.btn_back_set]

    # ─────────────────────────────────────────────────────────────────────────
    # CALLBACK ФУНКЦИИ (ДЕЙСТВИЯ КНОПОК)
    # ─────────────────────────────────────────────────────────────────────────
    def play_bot(self):
        """Запуск одиночной игры"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.result = "PLAY_BOT"
        self.running = False

    def play_online(self):
        """Переход в онлайн меню"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.state = "ONLINE"

    def host_game(self):
        """Создание сервера"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.result = "HOST"
        self.running = False

    def join_game(self):
        """Переход к вводу IP"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.state = "CONNECTING"
        self.ip_input.clear()

    def open_settings(self):
        """Открытие настроек"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.state = "SETTINGS"
        # Обновляем текст кнопки сложности
        self.btn_diff.set_text(f"Сложность: {self.settings['difficulty']}")

    def back_to_main(self):
        """Возврат в главное меню"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.state = "MAIN"

    def exit_game(self):
        """Выход из игры"""
        if self.sound_manager:
            self.sound_manager.play_click()
        self.save_settings()
        self.result = "EXIT"
        self.running = False

    def volume_up(self):
        """Увеличение громкости"""
        self.settings["volume"] = min(100, self.settings["volume"] + 10)
        if self.sound_manager:
            self.sound_manager.play_click()
            self.sound_manager.set_volume(self.settings["volume"])

    def volume_down(self):
        """Уменьшение громкости"""
        self.settings["volume"] = max(0, self.settings["volume"] - 10)
        if self.sound_manager:
            self.sound_manager.play_click()
            self.sound_manager.set_volume(self.settings["volume"])

    def toggle_difficulty(self):
        """Переключение сложности"""
        difficulties = ["Easy", "Normal", "Hard", "Ultra"]
        current_idx = difficulties.index(self.settings["difficulty"])
        self.settings["difficulty"] = difficulties[(current_idx + 1) % len(difficulties)]
        self.btn_diff.set_text(f"Сложность: {self.settings['difficulty']}")
        if self.sound_manager:
            self.sound_manager.play_click()

    # ─────────────────────────────────────────────────────────────────────────
    # ОТРИСОВКА
    # ─────────────────────────────────────────────────────────────────────────
    def draw_main_menu(self):
        """Отрисовка главного меню"""
        self.screen.fill(COLOR_BG)
        
        # Заголовок с эффектом
        title = self.font_large.render("PING-PONG ULTRA", True, COLOR_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)
        
        # Подзаголовок
        subtitle = self.font_small.render("Ultimate Network Pong Experience", True, (100, 100, 100))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 170))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.main_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

    def draw_online_menu(self):
        """Отрисовка онлайн меню"""
        self.screen.fill(COLOR_BG)
        
        title = self.font_large.render("ОНЛАЙН ИГРА", True, COLOR_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        if self.state == "ONLINE":
            for btn in self.online_buttons:
                btn.check_hover(mouse_pos)
                btn.draw(self.screen)
        
        elif self.state == "CONNECTING":
            # Поле ввода IP
            self.ip_input.draw(self.screen)
            
            hint = self.font_small.render("Введите IP и нажмите ENTER", True, COLOR_TEXT)
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, 410))
            self.screen.blit(hint, hint_rect)
            
            # Кнопка назад
            self.btn_back_online.check_hover(mouse_pos)
            self.btn_back_online.draw(self.screen)

    def draw_settings_menu(self):
        """Отрисовка меню настроек"""
        self.screen.fill(COLOR_BG)
        
        title = self.font_large.render("НАСТРОЙКИ", True, COLOR_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Громкость
        vol_text = self.font_small.render(f"Громкость: {self.settings['volume']}%", True, COLOR_TEXT)
        vol_rect = vol_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(vol_text, vol_rect)
        
        # Сложность
        diff_text = self.font_small.render(f"Сложность: {self.settings['difficulty']}", True, COLOR_TEXT)
        diff_rect = diff_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(diff_text, diff_rect)
        
        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.settings_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

    # ─────────────────────────────────────────────────────────────────────────
    # ГЛАВНЫЙ ЦИКЛ МЕНЮ
    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        """
        Запускает меню и возвращает выбор пользователя.
        Возвращаемые значения:
        - "PLAY_BOT" : Одиночная игра
        - "HOST"     : Создать сервер
        - "JOIN:IP"  : Подключиться к IP
        - "EXIT"     : Выход
        - None       : Отмена/возврат
        """
        self.running = True
        self.result = None
        
        while self.running:
            dt = self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            
            # ─────────────────────────────────────────────────────────────
            # ОБРАБОТКА СОБЫТИЙ
            # ─────────────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = "EXIT"
                    self.running = False
                
                # Главное меню
                if self.state == "MAIN":
                    for btn in self.main_buttons:
                        if btn.handle_event(event):
                            btn.callback()
                
                # Онлайн меню
                elif self.state == "ONLINE":
                    for btn in self.online_buttons:
                        if btn.handle_event(event):
                            btn.callback()
                
                # Подключение (ввод IP)
                elif self.state == "CONNECTING":
                    ip = self.ip_input.handle_event(event)
                    if ip and len(ip) > 7:  # Минимальная длина IP
                        self.result = f"JOIN:{ip}"
                        self.running = False
                    
                    if self.btn_back_online.handle_event(event):
                        self.btn_back_online.callback()
                    
                    # Анимация курсора
                    self.ip_input.update_cursor(dt)
                
                # Настройки
                elif self.state == "SETTINGS":
                    for btn in self.settings_buttons:
                        if btn.handle_event(event):
                            btn.callback()
            
            # ─────────────────────────────────────────────────────────────
            # ОТРИСОВКА
            # ─────────────────────────────────────────────────────────────
            if self.state == "MAIN":
                self.draw_main_menu()
            elif self.state == "ONLINE":
                self.draw_online_menu()
            elif self.state == "CONNECTING":
                self.draw_online_menu()
            elif self.state == "SETTINGS":
                self.draw_settings_menu()
            
            pygame.display.flip()
        
        # Сохранение настроек при выходе из меню
        self.save_settings()
        
        return self.result