import json
import os
import pyautogui
import screeninfo

def get_virtual_desktop_bounds():
    """
    Detecta o Virtual Desktop Bounding Box (caixa delimitadora de todas as telas combinadas).
    Retorna um dicionário com: min_x, min_y, max_x, max_y, total_width, total_height
    
    Exemplo: Se há dois monitores (1920x1080 à esquerda e 1920x1080 à direita):
        min_x = 0, min_y = 0, max_x = 3840, max_y = 1080
        total_width = 3840, total_height = 1080
    
    Se há um monitor à esquerda do principal (coordenadas negativas):
        min_x = -1920, min_y = 0, max_x = 1920, max_y = 1080
        total_width = 3840, total_height = 1080
    """
    try:
        monitors = screeninfo.get_monitors()
        if not monitors:
            # Fallback para pyautogui se screeninfo falhar
            width, height = pyautogui.size()
            return {
                'min_x': 0,
                'min_y': 0,
                'max_x': width,
                'max_y': height,
                'total_width': width,
                'total_height': height
            }
        
        # Encontrar os limites de todas as telas
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        total_width = max_x - min_x
        total_height = max_y - min_y
        
        return {
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y,
            'total_width': total_width,
            'total_height': total_height
        }
    except Exception as e:
        # Fallback para pyautogui em caso de erro
        print(f"Warning: Could not detect multi-monitor setup: {e}. Using primary screen only.")
        width, height = pyautogui.size()
        return {
            'min_x': 0,
            'min_y': 0,
            'max_x': width,
            'max_y': height,
            'total_width': width,
            'total_height': height
        }

def get_screen_resolution():
    """
    Mantido para compatibilidade, mas agora retorna o Virtual Desktop Bounding Box.
    Retorna uma tupla (total_width, total_height) para compatibilidade com código antigo.
    """
    bounds = get_virtual_desktop_bounds()
    return (bounds['total_width'], bounds['total_height'])

def normalize_coordinate(value, offset, total_size):
    """
    Normaliza uma coordenada usando offset e tamanho total.
    
    Fórmula: Normalizado = (ValorOriginal - Offset) / TamanhoTotal
    
    Args:
        value: Coordenada original (pode ser negativa)
        offset: Offset mínimo (min_x ou min_y)
        total_size: Tamanho total (total_width ou total_height)
    
    Returns:
        Float normalizado entre 0 e 1
    """
    if total_size == 0:
        return 0.0
    normalized = (value - offset) / total_size
    # Garantir que está entre 0 e 1
    return max(0.0, min(1.0, normalized))

def denormalize_coordinate(normalized_value, offset, total_size):
    """
    Converte uma coordenada normalizada de volta para coordenada absoluta.
    
    Fórmula: ValorOriginal = (Normalizado * TamanhoTotal) + Offset
    
    Args:
        normalized_value: Valor normalizado entre 0 e 1
        offset: Offset mínimo (min_x ou min_y)
        total_size: Tamanho total (total_width ou total_height)
    
    Returns:
        Coordenada absoluta (pode ser negativa)
    """
    return int((normalized_value * total_size) + offset)

def save_json(filepath, data):
    """Saves data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_json(filepath):
    """Loads data from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
