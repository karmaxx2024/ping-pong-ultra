# game.py
# 🎮 Одиночная игра с ботом

import pygame
import random
import sys
from config import *
from menu import Menu
from sound_manager import SoundManager

class Paddle:
    """Класс ракетки игрока или бота"""
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = PADDLE_SPEED
        self.score = 0

    def move(self, dy):
        """Перемещение ракетки по вертикали"""
        self.rect.y += dy
        # Ограничение, чтобы не уходила за экран
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def reset(self, y):
        """Сброс позиции ракетки"""
        self.rect.y = y

    def draw(self, screen):
        """Отрисовка ракетки"""
        pygame.draw.rect(screen, COLOR_PADDLE_1, self.rect)
        # Неоновая обводка
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2)


class Ball:
    """Класс мяча"""
    def __init__(self):
        self.reset()

    def reset(self):
        """Сброс мяча в центр"""
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        # Случайное направление подачи
        self.dx = BALL_SPEED_BASE * random.choice([1, -1])
        self.dy = BALL_SPEED_BASE * random.choice([1, -1])

    def update(self, player, bot, sound_mgr):
        """Обновление позиции и физика мяча"""
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Отскок от верха и низа
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.dy *= -1
            sound_mgr.play_hit()

        # Отскок от ракеток
        if self.rect.colliderect(player.rect):
            self.dx *= -1.05  # Ускорение при ударе
            self.rect.left = player.rect.right  # Чтобы не застрял
            sound_mgr.play_hit()
        
        if self.rect.colliderect(bot.rect):
            self.dx *= -1.05
            self.rect.right = bot.rect.left
            sound_mgr.play_hit()

        # Гол (выход за пределы слева или справа)
        if self.rect.left <= 0:
            sound_mgr.play_score()
            return "bot_score"
        if self.rect.right >= SCREEN_WIDTH:
            sound_mgr.play_score()
            return "player_score"
        
        return None

    def draw(self, screen):
        """Отрисовка мяча"""
        pygame.draw.rect(screen, COLOR_BALL, self.rect)
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2)


class SinglePlayerGame:
    """Основной класс одиночной игры"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"{TITLE} - Single Player")
        self.clock = pygame.time.Clock()
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 74)
        self.font_small = pygame.font.Font(None, 36)
        
        # Менеджеры
        self.sound_mgr = SoundManager()
        self.menu = Menu(self.screen, self.sound_mgr)
        
        # Состояния
        self.game_running = True
        self.in_menu = True
        
        # Настройки сложности
        self.difficulty_speed = {
            "Easy": 0.5,
            "Normal": 0.85,
            "Hard": 1.0,
            "Ultra": 1.2
        }

    def run(self):
        """Главный цикл запуска"""
        while self.game_running:
            if self.in_menu:
                # Запускаем меню и ждем выбора
                choice = self.menu.run()
                self.handle_menu_choice(choice)
            else:
                # Запускаем игровой процесс
                self.run_game()
        
        pygame.quit()
        sys.exit()

    def handle_menu_choice(self, choice):
        """Обработка выбора в меню"""
        if choice == "PLAY_BOT":
            self.in_menu = False
        elif choice == "EXIT":
            self.game_running = False
        elif choice is None:
            self.game_running = False

    def run_game(self):
        """Игровой цикл"""
        # Инициализация объектов
        player = Paddle(30, SCREEN_HEIGHT // 2 - 50)
        bot = Paddle(SCREEN_WIDTH - 45, SCREEN_HEIGHT // 2 - 50)
        ball = Ball()
        
        score_player = 0
        score_bot = 0
        
        game_running = True
        game_over = False
        winner = None

        # Получаем множитель скорости бота из настроек меню
        diff_key = self.menu.settings.get("difficulty", "Normal")
        bot_speed_multiplier = self.difficulty_speed.get(diff_key, 0.85)

        while game_running:
            self.clock.tick(FPS)
            
            # --- Обработка событий ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
                    self.in_menu = True
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_running = False
                        self.in_menu = True  # Вернуться в меню

            # --- Управление игроком ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                player.move(-player.speed)
            if keys[pygame.K_DOWN]:
                player.move(player.speed)
            
            # --- Логика Бота ---
            # Бот пытается выровнять центр ракетки по центру мяча
            bot_center = bot.rect.centery
            ball_center = ball.rect.centery
            
            # Зона мертвой зоны (чтобы бот не дрожал)
            if abs(ball_center - bot_center) > 10:
                if ball_center < bot_center:
                    bot.move(-bot.speed * bot_speed_multiplier)
                else:
                    bot.move(bot.speed * bot_speed_multiplier)
            
            # --- Обновление мяча ---
            result = ball.update(player, bot, self.sound_mgr)
            
            if result == "player_score":
                score_player += 1
                ball.reset()
            elif result == "bot_score":
                score_bot += 1
                ball.reset()
            
            # --- Проверка победы ---
            if score_player >= WIN_SCORE:
                winner = "player"
                game_over = True
                game_running = False
                self.sound_mgr.play_win()
            elif score_bot >= WIN_SCORE:
                winner = "bot"
                game_over = True
                game_running = False
                # Можно добавить звук поражения, если будет lose.wav

            # --- Отрисовка ---
            self.screen.fill(COLOR_BG)
            
            # Счет
            score_text = self.font_large.render(f"{score_player} : {score_bot}", True, COLOR_TEXT)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(score_text, score_rect)
            
            # Разделительная линия
            pygame.draw.aaline(self.screen, COLOR_TEXT, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            
            # Объекты
            player.draw(self.screen)
            bot.draw(self.screen)
            ball.draw(self.screen)
            
            # Подсказка
            hint = self.font_small.render("ESC - Меню", True, (100, 100, 100))
            self.screen.blit(hint, (10, 10))
            
            # Отображение сложности
            diff_text = self.font_small.render(f"Сложность: {diff_key}", True, (100, 100, 100))
            self.screen.blit(diff_text, (SCREEN_WIDTH - 150, 10))
            
            pygame.display.flip()

        # --- Экран победы/поражения ---
        if game_over:
            self.show_game_over_screen(winner)

    def show_game_over_screen(self, winner):
        """Экран конца игры"""
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.game_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        waiting = False
                        self.in_menu = True
            
            self.screen.fill(COLOR_BG)
            
            if winner == "player":
                text = self.font_large.render("ТЫ ПОБЕДИЛ!", True, COLOR_ACCENT)
            else:
                text = self.font_large.render("ТЫ ПРОИГРАЛ", True, (255, 50, 50))
            
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)
            
            hint = self.font_small.render("Нажми ESC или SPACE для продолжения", True, COLOR_TEXT)
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(hint, hint_rect)
            
            pygame.display.flip()


# --- Точка входа ---
if __name__ == "__main__":
    try:
        game = SinglePlayerGame()
        game.run()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        pygame.quit()
        sys.exit()