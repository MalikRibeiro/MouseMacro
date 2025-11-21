import customtkinter as ctk
import threading
import os
import time
import pynput.keyboard as pk
from tkinter import filedialog, messagebox
from src.recorder import Recorder
from src.player import Player
from src.utils import save_json, load_json
from src.overlay import StatusOverlay

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mouse Macro Automation")
        self.geometry("600x500")
        self.resizable(False, False)

        # State
        self.recorder = Recorder()
        self.player = Player()
        self.current_macro = None
        self.macro_path = None
        self.hotkeys = {
            'play': 'shift+1',
            'record': 'shift+3',
            'stop': 'esc',
            'pause': 'shift+2'
        }
        self.hotkey_listener = None
        
        # Overlay de status
        self.overlay = StatusOverlay(self)
        
        # Thread para atualizar contador de eventos
        self.event_counter_thread = None
        self.event_counter_running = False

        # Carregar configurações salvas antes de criar widgets
        self._load_settings()

        # UI Layout
        self._create_widgets()
        self._setup_hotkeys()
        
        # Protocol for closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        # Title
        self.lbl_title = ctk.CTkLabel(self, text="Mouse Macro Automation", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=20)

        # Status
        self.lbl_status = ctk.CTkLabel(self, text="Status: Ready", font=("Roboto", 14), text_color="gray")
        self.lbl_status.pack(pady=5)
        
        # Contador de eventos
        self.lbl_event_count = ctk.CTkLabel(self, text="Eventos: 0", font=("Roboto", 12), text_color="gray")
        self.lbl_event_count.pack(pady=2)

        # Controls Frame
        self.frame_controls = ctk.CTkFrame(self)
        self.frame_controls.pack(pady=20, padx=20, fill="x")

        self.btn_record = ctk.CTkButton(self.frame_controls, text="Record", command=self.toggle_recording, fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_record.pack(side="left", expand=True, padx=10, pady=10)

        self.btn_play = ctk.CTkButton(self.frame_controls, text="Play", command=self.play_macro, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_play.pack(side="left", expand=True, padx=10, pady=10)

        self.btn_stop = ctk.CTkButton(self.frame_controls, text="Stop", command=self.stop_all, fg_color="#f39c12", hover_color="#d35400")
        self.btn_stop.pack(side="left", expand=True, padx=10, pady=10)

        # Settings Frame
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=10, padx=20, fill="x")

        self.lbl_loops = ctk.CTkLabel(self.frame_settings, text="Loops:")
        self.lbl_loops.grid(row=0, column=0, padx=10, pady=10)
        self.entry_loops = ctk.CTkEntry(self.frame_settings, width=60)
        # Preenche com valor salvo ou padrão
        loops_value = getattr(self, '_saved_loops', '1')
        self.entry_loops.insert(0, loops_value)
        self.entry_loops.grid(row=0, column=1, padx=10, pady=10)

        self.lbl_interval = ctk.CTkLabel(self.frame_settings, text="Interval (s):")
        self.lbl_interval.grid(row=0, column=2, padx=10, pady=10)
        self.entry_interval = ctk.CTkEntry(self.frame_settings, width=60)
        # Preenche com valor salvo ou padrão
        interval_value = getattr(self, '_saved_interval', '0')
        self.entry_interval.insert(0, interval_value)
        self.entry_interval.grid(row=0, column=3, padx=10, pady=10)
        
        # Carrega macro automaticamente se houver caminho salvo
        saved_macro_path = getattr(self, '_saved_macro_path', None)
        if saved_macro_path and os.path.exists(saved_macro_path):
            try:
                self.current_macro = load_json(saved_macro_path)
                self.macro_path = saved_macro_path
                # Atualiza status após widgets serem criados
                self.after(100, lambda: self.lbl_status.configure(
                    text=f"Loaded: {os.path.basename(saved_macro_path)}", 
                    text_color="white"
                ))
            except Exception as e:
                print(f"Warning: Could not auto-load macro from {saved_macro_path}: {e}")

        # File Operations
        self.frame_files = ctk.CTkFrame(self)
        self.frame_files.pack(pady=10, padx=20, fill="x")

        self.btn_save = ctk.CTkButton(self.frame_files, text="Save Macro", command=self.save_macro)
        self.btn_save.pack(side="left", expand=True, padx=10, pady=10)

        self.btn_load = ctk.CTkButton(self.frame_files, text="Load Macro", command=self.load_macro)
        self.btn_load.pack(side="left", expand=True, padx=10, pady=10)
        
        # Hotkey Config
        self.btn_hotkeys = ctk.CTkButton(self, text="Configure Hotkeys", command=self.configure_hotkeys, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
        self.btn_hotkeys.pack(pady=10)

    def _setup_hotkeys(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        try:
            # Convert user-friendly hotkeys to pynput format
            # Usar self.after(0, ...) para garantir thread safety (chamadas de GUI na thread principal)
            hotkey_map = {
                self._parse_hotkey(self.hotkeys['record']): lambda: self.after(0, self.toggle_recording),
                self._parse_hotkey(self.hotkeys['play']): lambda: self.after(0, self.play_macro),
                self._parse_hotkey(self.hotkeys['stop']): lambda: self.after(0, self.stop_all),
                self._parse_hotkey(self.hotkeys['pause']): lambda: self.after(0, self.toggle_pause)
            }
            
            self.hotkey_listener = pk.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Error setting hotkeys: {e}")

    def _parse_hotkey(self, hotkey_str):
        # Convert "shift+1" to "<shift>+1" for pynput
        parts = hotkey_str.lower().split('+')
        parsed_parts = []
        special_keys = ['shift', 'ctrl', 'alt', 'cmd', 'esc', 'enter', 'tab', 'space', 'backspace', 'delete', 'up', 'down', 'left', 'right', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']
        
        for part in parts:
            part = part.strip()
            if part in special_keys:
                parsed_parts.append(f"<{part}>")
            else:
                parsed_parts.append(part)
        
        return '+'.join(parsed_parts)

    def _countdown(self, seconds, callback, status_text="Iniciando"):
        """Executa contagem regressiva e chama callback ao final."""
        if seconds > 0:
            self.lbl_status.configure(text=f"{status_text} em {seconds}...", text_color="orange")
            self.after(1000, lambda: self._countdown(seconds - 1, callback, status_text))
        else:
            self.lbl_status.configure(text="GO!", text_color="green")
            self.after(300, callback)  # Pequeno delay antes de executar
    
    def toggle_recording(self):
        if self.player.is_playing:
            self.lbl_status.configure(text="Cannot record while playing!", text_color="red")
            return

        if not self.recorder.is_recording:
            # Contagem regressiva antes de iniciar
            self._countdown(3, self._start_recording, "Iniciando gravação")
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Inicia a gravação após contagem regressiva."""
        self.recorder.start()
        self.btn_record.configure(text="Stop Recording")
        pause_hotkey = self.hotkeys.get('pause', 'Shift+2').upper()
        self.lbl_status.configure(text=f"Status: Gravando... ({pause_hotkey} para Pausar)", text_color="red")
        self.overlay.show_recording()
        self.minimize_window()
        self._start_event_counter()
    
    def _stop_recording(self):
        """Para a gravação."""
        data = self.recorder.stop()
        self.current_macro = data
        self.btn_record.configure(text="Record")
        event_count = len(data.get("events", [])) if data else 0
        self.lbl_status.configure(text=f"Status: Recording Finished ({event_count} eventos)", text_color="green")
        self.lbl_event_count.configure(text=f"Eventos: {event_count}")
        self.overlay.hide()
        self.restore_window()
        self._stop_event_counter()
        self.save_macro_prompt()
    
    def _start_event_counter(self):
        """Inicia thread para atualizar contador de eventos em tempo real."""
        if self.event_counter_running:
            return
        self.event_counter_running = True
        
        def update_counter():
            while self.event_counter_running and self.recorder.is_recording:
                with self.recorder._lock:
                    count = len(self.recorder.events)
                self.after(0, lambda c=count: self.lbl_event_count.configure(text=f"Eventos: {c}"))
                time.sleep(0.5)  # Atualiza a cada 0.5 segundos
        
        self.event_counter_thread = threading.Thread(target=update_counter, daemon=True)
        self.event_counter_thread.start()
    
    def _stop_event_counter(self):
        """Para a thread de contador de eventos."""
        self.event_counter_running = False

    def play_macro(self):
        if self.recorder.is_recording:
            self.lbl_status.configure(text="Cannot play while recording!", text_color="red")
            return
        
        if not self.current_macro:
            self.load_macro()
            if not self.current_macro:
                return

        try:
            loops = int(self.entry_loops.get())
            interval = float(self.entry_interval.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Loop or Interval values.")
            return

        # Contagem regressiva antes de iniciar
        self._countdown(3, lambda: self._start_playback(loops, interval), "Iniciando reprodução")
    
    def _start_playback(self, loops, interval):
        """Inicia a reprodução após contagem regressiva."""
        pause_hotkey = self.hotkeys.get('pause', 'Shift+2').upper()
        self.lbl_status.configure(text=f"Status: Reproduzindo... ({pause_hotkey} para Pausar)", text_color="green")
        self.overlay.show_playing()
        self.minimize_window()
        
        def on_finish():
            self.lbl_status.configure(text="Status: Playback Finished", text_color="gray")
            self.overlay.hide()
            self.restore_window()

        self.player.play(self.current_macro, loops, interval, on_finish)

    def stop_all(self):
        if self.recorder.is_recording:
            self._stop_recording()
        if self.player.is_playing:
            self.player.stop()
            self.lbl_status.configure(text="Status: Stopped", text_color="orange")
            self.overlay.hide()
    
    def toggle_pause(self):
        """Alterna entre pausar e retomar (gravação ou reprodução)."""
        if self.recorder.is_recording:
            self.recorder.toggle_pause()
            pause_hotkey = self.hotkeys.get('pause', 'Shift+2').upper()
            if self.recorder.is_paused:
                self.lbl_status.configure(text=f"Status: Pausado ({pause_hotkey} para Retomar)", text_color="orange")
                self.overlay.show_paused()
            else:
                self.lbl_status.configure(text=f"Status: Gravando... ({pause_hotkey} para Pausar)", text_color="red")
                self.overlay.show_recording()
        elif self.player.is_playing:
            self.player.toggle_pause()
            pause_hotkey = self.hotkeys.get('pause', 'Shift+2').upper()
            if self.player.is_paused:
                self.lbl_status.configure(text=f"Status: Pausado ({pause_hotkey} para Retomar)", text_color="orange")
                self.overlay.show_paused()
            else:
                self.lbl_status.configure(text=f"Status: Reproduzindo... ({pause_hotkey} para Pausar)", text_color="green")
                self.overlay.show_playing()
        else:
            # Não há nada para pausar
            return

    def save_macro(self):
        if not self.current_macro:
            messagebox.showwarning("Warning", "No macro recorded to save.")
            return
        
        filename = filedialog.asksaveasfilename(
            initialdir="macros",
            title="Save Macro",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            save_json(filename, self.current_macro)
            self.macro_path = filename
            # Salva o caminho da macro nas configurações
            self._save_settings()
            messagebox.showinfo("Success", f"Macro saved to {filename}")

    def save_macro_prompt(self):
        if messagebox.askyesno("Save", "Do you want to save the recorded macro?"):
            self.save_macro()

    def load_macro(self):
        filename = filedialog.askopenfilename(
            initialdir="macros",
            title="Load Macro",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            try:
                self.current_macro = load_json(filename)
                self.macro_path = filename
                self.lbl_status.configure(text=f"Loaded: {os.path.basename(filename)}", text_color="white")
                # Salva o caminho da macro nas configurações
                self._save_settings()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load macro: {e}")

    def configure_hotkeys(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Configure Hotkeys")
        dialog.geometry("300x250")
        dialog.attributes('-topmost', True)

        entries = {}
        for i, (name, key) in enumerate(self.hotkeys.items()):
            label_text = name.capitalize()
            if name == 'pause':
                label_text = 'Pause/Resume'
            ctk.CTkLabel(dialog, text=label_text).pack(pady=5)
            entry = ctk.CTkEntry(dialog)
            entry.insert(0, key)
            entry.pack(pady=5)
            entries[name] = entry

        def save():
            for name, entry in entries.items():
                self.hotkeys[name] = entry.get()
            self._setup_hotkeys()
            # Salva as hotkeys atualizadas nas configurações
            self._save_settings()
            dialog.destroy()
            messagebox.showinfo("Success", "Hotkeys updated!")

        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)

    def minimize_window(self):
        self.iconify()
        # Overlay já é mostrado pelos métodos específicos

    def restore_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.overlay.hide()

    def _load_settings(self):
        """Carrega configurações salvas do arquivo settings.json."""
        settings_path = "settings.json"
        
        if not os.path.exists(settings_path):
            # Arquivo não existe, usa valores padrão
            return
        
        try:
            settings = load_json(settings_path)
            
            # Carrega hotkeys personalizadas
            if 'hotkeys' in settings and isinstance(settings['hotkeys'], dict):
                # Atualiza apenas as hotkeys que existem no dicionário padrão
                for key in self.hotkeys:
                    if key in settings['hotkeys']:
                        self.hotkeys[key] = settings['hotkeys'][key]
            
            # Armazena valores para preencher nos campos após criar widgets
            self._saved_loops = settings.get('loops', '1')
            self._saved_interval = settings.get('interval', '0')
            self._saved_macro_path = settings.get('last_macro_path', None)
            
        except Exception as e:
            # Se houver erro ao carregar (arquivo corrompido), ignora e usa padrões
            print(f"Warning: Could not load settings: {e}. Using default values.")
            self._saved_loops = '1'
            self._saved_interval = '0'
            self._saved_macro_path = None
    
    def _save_settings(self):
        """Salva configurações atuais no arquivo settings.json."""
        settings_path = "settings.json"
        
        try:
            settings = {
                'hotkeys': self.hotkeys.copy(),
                'loops': self.entry_loops.get() if hasattr(self, 'entry_loops') else '1',
                'interval': self.entry_interval.get() if hasattr(self, 'entry_interval') else '0',
                'last_macro_path': self.macro_path if self.macro_path and os.path.exists(self.macro_path) else None
            }
            
            save_json(settings_path, settings)
        except Exception as e:
            # Se houver erro ao salvar, apenas imprime aviso (não trava o app)
            print(f"Warning: Could not save settings: {e}")
    
    def _on_close(self):
        self.stop_all()
        self._stop_event_counter()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        # Salva configurações antes de fechar
        self._save_settings()
        
        self.overlay.destroy()
        self.destroy()
