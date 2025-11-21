import customtkinter as ctk

class StatusOverlay(ctk.CTkToplevel):
    """
    Janela overlay semitransparente que exibe o status atual (REC, PLAY, PAUSE).
    Sempre no topo, sem bordas, posicionada no canto superior direito.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurações da janela overlay
        self.overrideredirect(True)  # Remove bordas e barra de título
        self.attributes('-topmost', True)  # Sempre no topo
        self.attributes('-alpha', 0.85)  # Semitransparente (85% opaco)
        
        # Tamanho pequeno e compacto
        self.geometry("120x60")
        
        # Posiciona no canto superior direito
        self._position_top_right()
        
        # Configura fundo escuro
        self.configure(fg_color=("gray10", "gray10"))
        
        # Label principal para exibir status
        self.lbl_status = ctk.CTkLabel(
            self,
            text="READY",
            font=("Roboto", 20, "bold"),
            text_color="gray"
        )
        self.lbl_status.pack(expand=True, fill="both")
        
        # Estado atual
        self.current_status = "ready"
        
        # Esconde inicialmente
        self.withdraw()
    
    def _position_top_right(self):
        """Posiciona a janela no canto superior direito da tela."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        x = screen_width - 130  # 120 (largura) + 10 (margem)
        y = 10
        self.geometry(f"120x60+{x}+{y}")
    
    def show_recording(self):
        """Exibe status de gravação (vermelho)."""
        self.current_status = "recording"
        self.lbl_status.configure(text="🔴 REC", text_color="#e74c3c")
        self.deiconify()
        self._position_top_right()
    
    def show_playing(self):
        """Exibe status de reprodução (verde)."""
        self.current_status = "playing"
        self.lbl_status.configure(text="▶️ PLAY", text_color="#2ecc71")
        self.deiconify()
        self._position_top_right()
    
    def show_paused(self):
        """Exibe status de pausado (amarelo)."""
        self.current_status = "paused"
        self.lbl_status.configure(text="⏸️ PAUSE", text_color="#f39c12")
        self.deiconify()
        self._position_top_right()
    
    def hide(self):
        """Esconde o overlay."""
        self.withdraw()
        self.current_status = "ready"
    
    def update_status(self, status):
        """
        Atualiza o status do overlay.
        
        Args:
            status: "recording", "playing", "paused", ou "ready"
        """
        if status == "recording":
            self.show_recording()
        elif status == "playing":
            self.show_playing()
        elif status == "paused":
            self.show_paused()
        else:
            self.hide()

