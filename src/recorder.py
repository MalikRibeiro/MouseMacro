import time
import threading
import pynput.mouse
import pynput.keyboard
from .utils import get_virtual_desktop_bounds, normalize_coordinate, is_modifier_key

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.events = []
        self.start_time = 0
        self.virtual_bounds = None  # Armazena os limites do desktop virtual
        self.mouse_listener = None
        self.keyboard_listener = None
        self.keyboard_listener = None
        self._lock = threading.Lock()
        self._modifier_lock = threading.Lock()
        self._pressed_modifiers = set()
        self.pause_event = threading.Event()  # Event para pausar/reiniciar gravação
        self.pause_event.set()  # Inicia não pausado (set = não pausado)
        self.is_paused = False
        
        # Optimization state
        self.last_move_time = 0
        self.last_move_pos = (0, 0)

    def start(self):
        if self.is_recording:
            return
        
        self.is_recording = True
        self.is_paused = False
        self.pause_event.set()  # Garante que não está pausado ao iniciar
        self.events = []
        self.start_time = time.time()
        # Captura a geometria atual de todas as telas (Virtual Desktop Bounding Box)
        self.virtual_bounds = get_virtual_desktop_bounds()
        
        # Reset optimization state
        self.last_move_time = self.start_time
        self.last_move_pos = pynput.mouse.Controller().position
        with self._modifier_lock:
            self._pressed_modifiers.clear()
        
        self.mouse_listener = pynput.mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.keyboard_listener = pynput.keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        print("Recording started...")

    def stop(self):
        if not self.is_recording:
            return None
            
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        print("Recording stopped.")
        self._report_unreleased_modifiers()
        self.is_paused = False
        self.pause_event.set()  # Reseta o estado de pausa
        return {
            "virtual_bounds": self.virtual_bounds,  # Salva a geometria virtual no JSON
            "events": self.events
        }
    
    def pause(self):
        """Pausa a gravação (ignora eventos enquanto pausado)."""
        if self.is_recording and not self.is_paused:
            self.pause_event.clear()  # clear = pausado
            self.is_paused = True
            print("Recording paused.")
    
    def resume(self):
        """Retoma a gravação."""
        if self.is_recording and self.is_paused:
            self.pause_event.set()  # set = não pausado (retoma)
            self.is_paused = False
            print("Recording resumed.")
    
    def toggle_pause(self):
        """Alterna entre pausado e retomado."""
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    def _on_move(self, x, y):
        """Callback para eventos de movimento do mouse com otimização de threshold."""
        if not self.is_recording or not self.pause_event.is_set():
            return  # Ignora eventos se não estiver gravando ou se estiver pausado
        
        current_time = time.time()
        dist = ((x - self.last_move_pos[0])**2 + (y - self.last_move_pos[1])**2)**0.5
        
        # Threshold/Otimização: só registra se distância > 5px ou tempo > 0.1s
        if dist > 5 or (current_time - self.last_move_time) > 0.1:
            # Normaliza usando o Virtual Desktop Bounding Box
            self._add_event({
                'action': 'move',
                'x': normalize_coordinate(x, self.virtual_bounds['min_x'], self.virtual_bounds['total_width']),
                'y': normalize_coordinate(y, self.virtual_bounds['min_y'], self.virtual_bounds['total_height'])
            })
            self.last_move_pos = (x, y)
            self.last_move_time = current_time

    def _add_event(self, event_data):
        """Adiciona um evento à lista de eventos com thread lock."""
        with self._lock:
            if not self.is_recording or not self.pause_event.is_set():
                return  # Não adiciona eventos se não estiver gravando ou se estiver pausado
            event_data['time'] = time.time() - self.start_time
            self.events.append(event_data)

    def _on_click(self, x, y, button, pressed):
        if self.is_recording and self.pause_event.is_set():
            # Normaliza usando o Virtual Desktop Bounding Box
            self._add_event({
                'action': 'press_btn' if pressed else 'release_btn',
                'button': str(button),
                'x': normalize_coordinate(x, self.virtual_bounds['min_x'], self.virtual_bounds['total_width']),
                'y': normalize_coordinate(y, self.virtual_bounds['min_y'], self.virtual_bounds['total_height'])
            })

    def _on_scroll(self, x, y, dx, dy):
        if self.is_recording and self.pause_event.is_set():
            self._add_event({
                'action': 'scroll',
                'dx': dx,
                'dy': dy
            })

    def _on_press(self, key):
        if self.is_recording and self.pause_event.is_set():
            try:
                key_val = key.char
            except AttributeError:
                key_val = str(key)
            if key_val is None:
                key_val = str(key)
            
            self._add_event({
                'action': 'press',
                'key': key_val
            })
            self._track_modifier_state(key_val, pressed=True)

    def _on_release(self, key):
        if self.is_recording and self.pause_event.is_set():
            try:
                key_val = key.char
            except AttributeError:
                key_val = str(key)
            if key_val is None:
                key_val = str(key)

            self._add_event({
                'action': 'release',
                'key': key_val
            })
            self._track_modifier_state(key_val, pressed=False)

    def _track_modifier_state(self, key_str, pressed):
        if not is_modifier_key(key_str):
            return
        with self._modifier_lock:
            if pressed:
                if key_str not in self._pressed_modifiers:
                    self._pressed_modifiers.add(key_str)
                    print(f"[Recorder] Modifier pressed: {key_str}")
            else:
                if key_str in self._pressed_modifiers:
                    self._pressed_modifiers.discard(key_str)
                    print(f"[Recorder] Modifier released: {key_str}")

    def _report_unreleased_modifiers(self):
        with self._modifier_lock:
            if not self._pressed_modifiers:
                return
            stuck = list(self._pressed_modifiers)
            self._pressed_modifiers.clear()
        print(f"[Recorder] Warning: {len(stuck)} modifier(s) still pressed at stop: {', '.join(stuck)}")
