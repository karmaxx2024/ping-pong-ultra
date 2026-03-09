# sound_manager.py
import pygame
import os
import json

class SoundManager:
    """Управление звуками игры"""
    
    def __init__(self, settings_file="settings.json"):
        """Инициализация микшера и загрузка настроек"""
        pygame.mixer.init()
        
        self.sounds = {}
        self.enabled = True
        self.volume = 0.7  # Громкость по умолчанию (70%)
        
        # Загрузка настроек из файла
        self.settings_file = settings_file
        self.load_settings()
        
        # Загрузка звуковых файлов
        self.load_sounds()

    def load_settings(self):
        """Загрузка настроек из JSON файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.volume = settings.get("volume", 70) / 100
                    self.enabled = settings.get("sound_enabled", True)
            except Exception as e:
                print(f"⚠️ Ошибка чтения настроек: {e}")

    def save_settings(self):
        """Сохранение текущих настроек в JSON файл"""
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            
            settings["volume"] = int(self.volume * 100)
            settings["sound_enabled"] = self.enabled
            
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения настроек: {e}")

    def load_sounds(self):
        """Загрузка звуковых файлов из папки assets/sounds/"""
        sound_files = {
            "hit": "assets/sounds/hit.wav",
            "score": "assets/sounds/score.wav",
            "click": "assets/sounds/click.wav",
            "win": "assets/sounds/win.wav"
        }
        
        print("🔊 Загрузка звуков...")
        for name, path in sound_files.items():
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    self.sounds[name].set_volume(self.volume)
                    print(f"✅ {name}: загружен")
                except Exception as e:
                    print(f"❌ {name}: ошибка загрузки ({e})")
                    self.sounds[name] = None
            else:
                print(f"⚠️ {name}: файл не найден ({path})")
                self.sounds[name] = None

    def play(self, sound_name):
        """Воспроизведение звука по имени"""
        if not self.enabled:
            return
        
        if sound_name in self.sounds:
            if self.sounds[sound_name]:
                try:
                    self.sounds[sound_name].play()
                except Exception as e:
                    print(f"⚠️ Ошибка воспроизведения {sound_name}: {e}")

    def play_hit(self):
        """Звук удара мяча о ракетку"""
        self.play("hit")

    def play_score(self):
        """Звук гола"""
        self.play("score")

    def play_click(self):
        """Звук клика в меню"""
        self.play("click")

    def play_win(self):
        """Звук победы"""
        self.play("win")

    def set_volume(self, volume_percent):
        """
        Установка громкости (0-100)
        :param volume_percent: Громкость в процентах
        """
        self.volume = max(0, min(100, volume_percent)) / 100
        
        # Обновляем громкость всех загруженных звуков
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)
        
        self.save_settings()

    def toggle_sound(self):
        """Включить/выключить звук"""
        self.enabled = not self.enabled
        self.save_settings()
        return self.enabled

    def get_volume(self):
        """Получить текущую громкость в процентах"""
        return int(self.volume * 100)

    def is_enabled(self):
        """Проверить, включен ли звук"""
        return self.enabled