# server.py
# 🟢 Сервер WebSocket для сетевой игры

import asyncio
import websockets
import json
import random
import socket
import sys
from config import *

# ─────────────────────────────────────────────────────────────────────────────
# КЛАСС ИГРОВОГО СЕРВЕРА
# ─────────────────────────────────────────────────────────────────────────────
class GameServer:
    def __init__(self):
        self.players = []  # [player1_ws, player2_ws]
        self.game_state = {
            "ball": {"x": SCREEN_WIDTH // 2, "y": SCREEN_HEIGHT // 2, "dx": 5, "dy": 5},
            "paddle1": SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
            "paddle2": SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
            "score": [0, 0],
            "status": "waiting"  # waiting, playing, ended
        }
        self.running = True
        self.winner = None

    def get_local_ip(self):
        """Получение локального IP-адреса"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    async def handle_player(self, websocket, path):
        """Обработка подключения игрока"""
        print(f"🟢 Подключение: {websocket.remote_address}")
        
        # Добавляем игрока
        if len(self.players) < 2:
            self.players.append(websocket)
            player_id = len(self.players) - 1
            await websocket.send(json.dumps({"type": "id", "id": player_id}))
            print(f"✅ Игрок {player_id + 1} подключился. Всего: {len(self.players)}/2")
            
            if len(self.players) == 2:
                self.game_state["status"] = "playing"
                print("🎮 Игра началась!")
                for p in self.players:
                    try:
                        await p.send(json.dumps({"type": "start"}))
                    except:
                        pass
        else:
            await websocket.send(json.dumps({"type": "full"}))
            await websocket.close()
            print("❌ Сервер полон!")
            return

        try:
            async for message in websocket:
                data = json.loads(message)
                
                # Получаем движение ракетки
                if data["type"] == "move":
                    player_id = data["id"]
                    key = f"paddle{player_id + 1}"
                    self.game_state[key] = data["y"]
                
                # Рассылаем состояние всем
                await self.broadcast()
                
        except websockets.exceptions.ConnectionClosed:
            print(f"🔴 Игрок отключился: {websocket.remote_address}")
            if websocket in self.players:
                self.players.remove(websocket)
            self.game_state["status"] = "waiting"
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    async def broadcast(self):
        """Отправка состояния всем игрокам"""
        if len(self.players) == 2:
            state_json = json.dumps(self.game_state)
            for player in self.players:
                try:
                    await player.send(state_json)
                except:
                    pass

    async def game_loop(self):
        """Обновление физики на сервере"""
        while self.running:
            if self.game_state["status"] == "playing":
                ball = self.game_state["ball"]
                
                # Движение мяча
                ball["x"] += ball["dx"]
                ball["y"] += ball["dy"]

                # Отскок от верха и низа
                if ball["y"] <= 0 or ball["y"] >= SCREEN_HEIGHT - BALL_SIZE:
                    ball["dy"] *= -1

                # Отскок от ракеток
                # Игрок 1 (слева)
                if (ball["x"] <= 30 + PADDLE_WIDTH and 
                    self.game_state["paddle1"] <= ball["y"] <= self.game_state["paddle1"] + PADDLE_HEIGHT):
                    ball["dx"] = abs(ball["dx"]) * 1.05  # Ускорение
                    ball["x"] = 30 + PADDLE_WIDTH + 1
                    
                # Игрок 2 (справа)
                if (ball["x"] >= SCREEN_WIDTH - 45 - PADDLE_WIDTH and 
                    self.game_state["paddle2"] <= ball["y"] <= self.game_state["paddle2"] + PADDLE_HEIGHT):
                    ball["dx"] = -abs(ball["dx"]) * 1.05
                    ball["x"] = SCREEN_WIDTH - 45 - PADDLE_WIDTH - 1

                # Ограничение скорости мяча
                max_speed = 15
                ball["dx"] = max(-max_speed, min(max_speed, ball["dx"]))
                ball["dy"] = max(-max_speed, min(max_speed, ball["dy"]))

                # Гол
                if ball["x"] <= 0:
                    self.game_state["score"][1] += 1
                    print(f"🎯 Гол! Игрок 2: {self.game_state['score'][1]}")
                    self.reset_ball()
                    
                if ball["x"] >= SCREEN_WIDTH - BALL_SIZE:
                    self.game_state["score"][0] += 1
                    print(f"🎯 Гол! Игрок 1: {self.game_state['score'][0]}")
                    self.reset_ball()

                # Проверка победы
                if self.game_state["score"][0] >= WIN_SCORE:
                    self.winner = 1
                    self.game_state["status"] = "ended"
                    await self.broadcast()
                    print("🏆 Игрок 1 победил!")
                    
                elif self.game_state["score"][1] >= WIN_SCORE:
                    self.winner = 2
                    self.game_state["status"] = "ended"
                    await self.broadcast()
                    print("🏆 Игрок 2 победил!")

                await self.broadcast()
            
            await asyncio.sleep(1 / FPS)

    def reset_ball(self):
        """Сброс мяча в центр"""
        self.game_state["ball"] = {
            "x": SCREEN_WIDTH // 2,
            "y": SCREEN_HEIGHT // 2,
            "dx": BALL_SPEED_BASE * random.choice([1, -1]),
            "dy": BALL_SPEED_BASE * random.choice([1, -1])
        }

    async def run(self):
        """Запуск сервера"""
        print()
        print("=" * 50)
        print("🟢 ЗАПУСК СЕРВЕРА")
        print("=" * 50)
        print(f"📡 IP для подключения: {self.get_local_ip()}")
        print(f"🔌 Порт: {SERVER_PORT}")
        print("=" * 50)
        print("⏳ Ожидание подключения второго игрока...")
        print("Нажмите Ctrl+C для остановки\n")
        
        server = await websockets.serve(self.handle_player, "0.0.0.0", SERVER_PORT)
        
        # Запускаем игровой цикл параллельно
        asyncio.create_task(self.game_loop())
        
        await server.wait_closed()


# ─────────────────────────────────────────────────────────────────────────────
# ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    try:
        server = GameServer()
        await server.run()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")
    finally:
        print("🔌 Сервер закрыт")

if __name__ == "__main__":
    asyncio.run(main())