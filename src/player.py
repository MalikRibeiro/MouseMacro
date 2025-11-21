import time
import threading
import pynput.mouse
import pynput.keyboard
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from .utils import get_virtual_desktop_bounds, denormalize_coordinate

# Control character map from original code
CONTROL_CHAR_MAP = {
    '\x01':'a', '\x02':'b', '\x03':'c', '\x04':'d', '\x05':'e', '\x06':'f', '\x07':'g', 
    '\x08':'h', '\x09':'i', '\x0a':'j', '\x0b':'k', '\x0c':'l', '\x0d':'m', '\x0e':'n', 
    '\x0f':'o', '\x10':'p', '\x11':'q', '\x12':'r', '\x13':'s', '\x14':'t', '\x15':'u', 
    '\x16':'v', '\x17':'w', '\x18':'x', '\x19':'y', '\x1a':'z'
}

class Player:
    def __init__(self):
        self.mouse = pynput.mouse.Controller()
        self.keyboard = pynput.keyboard.Controller()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()  # Event para pausar/reiniciar
        self.pause_event.set()  # Inicia não pausado (set = não pausado)
        self.is_playing = False
        self.is_paused = False
        self.thread = None

    def play(self, macro_data, loops=1, interval=0, on_finish=None):
        if self.is_playing:
            return
        
        self.stop_event.clear()
        self.pause_event.set()  # Garante que não está pausado ao iniciar
        self.is_playing = True
        self.is_paused = False
        
        self.thread = threading.Thread(
            target=self._play_worker,
            args=(macro_data, loops, interval, on_finish)
        )
        self.thread.start()
    
    def pause(self):
        """Pausa a reprodução."""
        if self.is_playing and not self.is_paused:
            self.pause_event.clear()  # clear = pausado
            self.is_paused = True
            print("Playback paused.")
    
    def resume(self):
        """Retoma a reprodução."""
        if self.is_playing and self.is_paused:
            self.pause_event.set()  # set = não pausado (retoma)
            self.is_paused = False
            print("Playback resumed.")
    
    def toggle_pause(self):
        """Alterna entre pausado e retomado."""
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    def stop(self):
        if self.is_playing:
            self.stop_event.set()
            # Wait for thread to finish? No, just signal.
            # The worker checks stop_event frequently.
            print("Stop signal sent to player.")

    def _play_worker(self, macro_data, loops, interval, on_finish):
        events = macro_data.get("events", [])
        
        # Lê os virtual_bounds do JSON original (gravado)
        recorded_bounds = macro_data.get("virtual_bounds")
        if not recorded_bounds:
            # Compatibilidade com macros antigas que não têm virtual_bounds
            # Assume que foi gravado em uma única tela sem offset
            recorded_bounds = {
                'min_x': 0,
                'min_y': 0,
                'total_width': macro_data.get("resolution", (1920, 1080))[0],
                'total_height': macro_data.get("resolution", (1920, 1080))[1]
            }
        
        # Detecta os current_virtual_bounds do computador onde está rodando
        current_bounds = get_virtual_desktop_bounds()
        
        try:
            for i in range(loops):
                if self.stop_event.is_set():
                    break
                
                print(f"Starting loop {i+1}/{loops}")
                last_time = 0.0
                
                for event in events:
                    if self.stop_event.is_set():
                        break
                    
                    # Verifica se está pausado - bloqueia até ser retomado
                    if not self.pause_event.is_set():
                        # Está pausado, espera até ser retomado (sem gastar CPU)
                        self.pause_event.wait()
                    
                    # Calculate delay
                    delay = max(0, event['time'] - last_time)
                    
                    # Wait with check for stop_event
                    if self.stop_event.wait(delay):
                        break
                    
                    # Verifica pausa novamente após o delay
                    if not self.pause_event.is_set():
                        self.pause_event.wait()
                    
                    self._execute_event(event, recorded_bounds, current_bounds)
                    last_time = event['time']
                    
                    # Small delay to prevent freezing if events are too fast?
                    # Original had ACTION_DELAY_SECONDS = 0.01
                    time.sleep(0.001) 

                if i < loops - 1:
                    if self.stop_event.wait(interval):
                        break
                        
        except Exception as e:
            print(f"Error during playback: {e}")
        finally:
            self.is_playing = False
            self.is_paused = False
            self.pause_event.set()  # Reseta o estado de pausa
            print("Playback finished.")
            if on_finish:
                on_finish()

    def _convert_coordinate(self, normalized_x, normalized_y, recorded_bounds, current_bounds):
        """
        Converte coordenadas normalizadas da gravação para coordenadas absolutas do sistema atual.
        Faz conversão proporcional se as resoluções forem diferentes.
        
        A coordenada normalizada (0-1) representa a posição relativa dentro do espaço virtual gravado.
        Esta função converte diretamente para a posição relativa equivalente no sistema atual.
        
        Args:
            normalized_x, normalized_y: Coordenadas normalizadas (0-1) da gravação
            recorded_bounds: Bounds do sistema onde foi gravado
            current_bounds: Bounds do sistema atual
        
        Returns:
            Tupla (x, y) ou None se a coordenada estiver fora dos limites válidos
        """
        # A coordenada normalizada já representa a posição relativa (0-1) dentro do espaço virtual
        # Converte diretamente para coordenada absoluta do sistema atual (com conversão proporcional)
        current_x = denormalize_coordinate(
            normalized_x,
            current_bounds['min_x'],
            current_bounds['total_width']
        )
        current_y = denormalize_coordinate(
            normalized_y,
            current_bounds['min_y'],
            current_bounds['total_height']
        )
        
        # Valida se a coordenada está dentro dos limites válidos
        if not self._is_coordinate_valid(current_x, current_y, current_bounds):
            print(f"Warning: Coordinate ({current_x}, {current_y}) is outside valid screen bounds. Skipping action.")
            return None
        
        return (current_x, current_y)
    
    def _is_coordinate_valid(self, x, y, bounds):
        """
        Verifica se uma coordenada está dentro dos limites válidos das telas.
        
        Args:
            x, y: Coordenadas a verificar
            bounds: Bounds do sistema atual
        
        Returns:
            True se a coordenada é válida, False caso contrário
        """
        return (bounds['min_x'] <= x < bounds['max_x'] and 
                bounds['min_y'] <= y < bounds['max_y'])
    
    def _execute_event(self, event, recorded_bounds, current_bounds):
        action = event['action']
        
        if action == 'move':
            coords = self._convert_coordinate(
                event.get('x', 0.5), 
                event.get('y', 0.5), 
                recorded_bounds, 
                current_bounds
            )
            if coords:
                self.mouse.position = coords
            
        elif action == 'press_btn':
            coords = self._convert_coordinate(
                event.get('x', 0.5), 
                event.get('y', 0.5), 
                recorded_bounds, 
                current_bounds
            )
            if coords:
                self.mouse.position = coords
                button = self._get_button_from_string(event['button'])
                self.mouse.press(button)
            
        elif action == 'release_btn':
            coords = self._convert_coordinate(
                event.get('x', 0.5), 
                event.get('y', 0.5), 
                recorded_bounds, 
                current_bounds
            )
            if coords:
                self.mouse.position = coords
                button = self._get_button_from_string(event['button'])
                self.mouse.release(button)
            
        elif action == 'press':
            key = self._get_key_from_string(event['key'])
            self.keyboard.press(key)
            
        elif action == 'release':
            key = self._get_key_from_string(event['key'])
            self.keyboard.release(key)
            
        elif action == 'scroll':
            # Verificar se as chaves 'dx' e 'dy' existem antes de executar
            dx = event.get('dx', 0)
            dy = event.get('dy', 0)
            self.mouse.scroll(dx, dy)

    def _get_key_from_string(self, key_str):
        if key_str in CONTROL_CHAR_MAP:
            return CONTROL_CHAR_MAP[key_str]
        if key_str.startswith('Key.'):
            return getattr(Key, key_str.split('.')[1])
        if key_str.startswith('<') and key_str.endswith('>'):
            try:
                return KeyCode(vk=int(key_str[1:-1]))
            except (ValueError, TypeError):
                return key_str
        return key_str

    def _get_button_from_string(self, button_str):
        return getattr(Button, button_str.split('.')[1])
