# client.py
# 🔵 Клиент WebSocket для сетевой игры

import pygame
import asyncio
import websockets
import json
import sys
from config import *

# ─────────────────────────────────────────────────────────────────────────────
# КЛАСС СЕТЕВОЙ ИГРЫ
# ─────────────────────────────────────────────────────────────────────────────
class NetworkGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"{TITLE} - ONLINE")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 74)
        self.font_small = pygame.font.Font(None, 36)
        
        self.player_id = None
        self.connected = False
        self.game_state = None
        self.websocket = None
        self.server_ip = ""
        self.running = True
        self.in_menu = True
        
        # Поле ввода IP
        self.input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 300, 40)
        self.input_text = ""
        self.input_active = False
        self.cursor_timer = 0
        self.show_cursor = True
        
        # Позиция ракетки
        self.paddle_y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2

    async def connect(self, ip):
        """Подключение к серверу"""
        try:
            uri = f"ws://{ip}:{SERVER_PORT}"
            print(f"🔵 Подключение к {uri}...")
            self.websocket = await websockets.connect(uri, timeout=5)
            self.connected = True
            print(f"✅ Подключено к {ip}")
            
            # Получаем ID игрока
            msg = await self.websocket.recv()
            data = json.loads(msg)
            
            if data["type"] == "id":
                self.player_id = data["id"]
                print(f"🎮 Вы игрок {self.player_id + 1}")
            elif data["type"] == "full":
                print("❌ Сервер полон!")
                self.connected = False
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            self.connected = False
            return False

    async def receive_updates(self):
        """Получение обновлений от сервера"""
        while self.connected and self.running:
            try:
                msg = await self.websocket.recv()
                self.game_state = json.loads(msg)
            except:
                break

    async def send_move(self, y):
        """Отправка позиции ракетки"""
        if self.connected and self.websocket and self.player_id is not None:
            try:
                await self.websocket.send(json.dumps({
                    "type": "move",
                    "id": self.player_id,
                    "y": y
                }))
            except:
                pass

    def draw_menu(self):
        """Отрисовка меню подключения"""
        self.screen.fill(COLOR_BG)
        
        # Заголовок
        title = self.font_large.render("ОНЛАЙН ИГРА", True, COLOR_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Подзаголовок
        info = self.font_small.render("Введите IP сервера:", True, COLOR_TEXT)
        info_rect = info.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(info, info_rect)
        
        # Поле ввода
        color = COLOR_ACCENT if self.input_active else COLOR_TEXT
        pygame.draw.rect(self.screen, color, self.input_box, 2)
        pygame.draw.rect(self.screen, COLOR_BG, self.input_box.inflate(-4, -4))
        
        display_text = self.input_text if self.input_text else "192.168.X.X"
        text_color = COLOR_TEXT if self.input_text else (100, 100, 100)
        text_surf = self.font_small.render(display_text, True, text_color)
        self.screen.blit(text_surf, (self.input_box.x + 10, self.input_box.y + 5))
        
        # Курсор
        if self.input_active and self.show_cursor:
            cursor_x = self.input_box.x + 10 + text_surf.get_width()
            pygame.draw.line(self.screen, COLOR_TEXT, 
                           (cursor_x, self.input_box.y + 5),
                           (cursor_x, self.input_box.y + 30), 2)
        
        # Подсказки
        hint1 = self.font_small.render("Нажми ENTER для подключения", True, COLOR_TEXT)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, 420))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = self.font_small.render("ESC - Назад", True, (100, 100, 100))
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, 460))
        self.screen.blit(hint2, hint2_rect)
        
        # Статус
        status = "🟢 ONLINE" if self.connected else "🔴 OFFLINE"
        status_color = COLOR_ACCENT if self.connected else (255, 50, 50)
        status_text = self.font_small.render(status, True, status_color)
        self.screen.blit(status_text, (10, 10))
        
        pygame.display.flip()

    def draw_game(self):
        """Отрисовка игры"""
        self.screen.fill(COLOR_BG)
        
        if self.game_state:
            # Счет
            score = self.game_state["score"]
            score_text = self.font_large.render(f"{score[0]} : {score[1]}", True, COLOR_TEXT)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(score_text, score_rect)
            
            # Сетка
            pygame.draw.aaline(self.screen, COLOR_TEXT, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            
            # Ракетки
            paddle1_y = self.game_state.get("paddle1", SCREEN_HEIGHT // 2 - 50)
            paddle2_y = self.game_state.get("paddle2", SCREEN_HEIGHT // 2 - 50)
            
            rect1 = pygame.Rect(30, paddle1_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            rect2 = pygame.Rect(SCREEN_WIDTH - 45, paddle2_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            
            pygame.draw.rect(self.screen, COLOR_PADDLE_1, rect1)
            pygame.draw.rect(self.screen, COLOR_PADDLE_2, rect2)
            
            # Обводка
            pygame.draw.rect(self.screen, COLOR_TEXT, rect1, 2)
            pygame.draw.rect(self.screen, COLOR_TEXT, rect2, 2)
            
            # Мяч
            ball = self.game_state.get("ball", {"x": 400, "y": 300})
            ball_rect = pygame.Rect(ball["x"], ball["y"], BALL_SIZE, BALL_SIZE)
            pygame.draw.rect(self.screen, COLOR_BALL, ball_rect)
            pygame.draw.rect(self.screen, COLOR_TEXT, ball_rect, 2)
            
            # Индикатор игрока
            if self.player_id == 0:
                marker = "ВЫ (Игрок 1)"
                marker_rect = pygame.Rect(20, paddle1_y, 5, PADDLE_HEIGHT)
            else:
                marker = "ВЫ (Игрок 2)"
                marker_rect = pygame.Rect(SCREEN_WIDTH - 25, paddle2_y, 5, PADDLE_HEIGHT)
            
            marker_text = self.font_small.render(marker, True, COLOR_ACCENT)
            self.screen.blit(marker_text, (10, SCREEN_HEIGHT - 40))
            
            # Статус игры
            status = self.game_state.get("status", "waiting")
            if status == "ended":
                end_text = self.font_large.render("ИГРА ОКОНЧЕНА", True, COLOR_ACCENT)
                end_rect = end_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                pygame.draw.rect(self.screen, COLOR_BG, end_rect.inflate(20, 20))
                self.screen.blit(end_text, end_rect)
        
        # Статус подключения
        status = "🟢 ONLINE" if self.connected else "🔴 OFFLINE"
        status_color = COLOR_ACCENT if self.connected else (255, 50, 50)
        status_text = self.font_small.render(status, True, status_color)
        self.screen.blit(status_text, (10, 10))
        
        # Подсказка
        hint = self.font_small.render("ESC - Меню", True, (100, 100, 100))
        self.screen.blit(hint, (SCREEN_WIDTH - 120, 10))
        
        pygame.display.flip()

    def draw_game_over(self, winner):
        """Экран конца игры"""
        self.screen.fill(COLOR_BG)
        
        if winner == self.player_id:
            text = self.font_large.render("ПОБЕДА!", True, COLOR_ACCENT)
        else:
            text = self.font_large.render("ПОРАЖЕНИЕ", True, (255, 50, 50))
        
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)
        
        hint = self.font_small.render("Нажми ESC для возврата", True, COLOR_TEXT)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(hint, hint_rect)
        
        pygame.display.flip()

    async def run(self):
        """Главный цикл"""
        while self.running:
            self.clock.tick(FPS)
            dt = self.clock.get_time()
            
            # Обновление курсора
            self.cursor_timer += dt
            if self.cursor_timer > 500:
                self.show_cursor = not self.show_cursor
                self.cursor_timer = 0
            
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if not self.connected:
                    # Меню подключения
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.input_active = self.input_box.collidepoint(event.pos)
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.input_text:
                                self.server_ip = self.input_text
                                success = await self.connect(self.server_ip)
                                if success:
                                    asyncio.create_task(self.receive_updates())
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                        else:
                            if len(self.input_text) < 15:
                                char = event.unicode
                                if char.isdigit() or char == '.':
                                    self.input_text += char
                else:
                    # Игра
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.connected = False
                            self.in_menu = True
                            if self.websocket:
                                await self.websocket.close()
            
            # Логика
            if self.connected and self.game_state:
                # Управление ракеткой
                keys = pygame.key.get_pressed()
                
                # Игрок 1: Стрелки, Игрок 2: W/S
                if self.player_id == 0:
                    if keys[pygame.K_UP]:
                        self.paddle_y -= PADDLE_SPEED
                    if keys[pygame.K_DOWN]:
                        self.paddle_y += PADDLE_SPEED
                else:
                    if keys[pygame.K_w]:
                        self.paddle_y -= PADDLE_SPEED
                    if keys[pygame.K_s]:
                        self.paddle_y += PADDLE_SPEED
                
                # Ограничения
                self.paddle_y = max(0, min(SCREEN_HEIGHT - PADDLE_HEIGHT, self.paddle_y))
                
                # Отправка позиции