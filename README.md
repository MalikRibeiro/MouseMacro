# 🖱️ Mouse Macro Automation

Um gravador e reprodutor de macros profissional para Windows, desenvolvido em Python com interface moderna (CustomTkinter). Projetado para alta precisão, suporte a múltiplos monitores e facilidade de uso.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![UI](https://img.shields.io/badge/UI-CustomTkinter-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## 🚀 Funcionalidades

- **Interface Moderna:** Visual estilo Windows 11 (Dark Mode) usando `customtkinter`.
- **Suporte Multi-Monitor:** Grava e reproduz movimentos através de todas as telas (Virtual Desktop), com conversão proporcional de resolução.
- **Overlay de Status:** Janela flutuante discreta que indica o estado atual (🔴 GRAVANDO, ▶️ REPRODUZINDO, ⏸️ PAUSADO).
- **Controle Total:** Funções de Gravar, Reproduzir, Parar e **Pausar/Retomar**.
- **Otimização Inteligente:** Algoritmo de *threshold* para evitar arquivos de macro gigantescos.
- **Persistência:** Salva automaticamente suas preferências (loops, intervalos, atalhos e última macro usada).
- **Contagem Regressiva:** Timer de 3 segundos antes de iniciar para preparação do usuário.
- **Hotkeys Globais:** Controle o software mesmo minimizado.

## 🎮 Atalhos Padrão

| Ação | Atalho Padrão | Descrição |
| :--- | :--- | :--- |
| **Gravar** | `Shift+3` | Inicia ou para a gravação. |
| **Reproduzir** | `Shift+1` | Inicia a reprodução da macro carregada. |
| **Pausar/Retomar** | `Shift+2` | Suspende temporariamente a gravação ou reprodução. |
| **Parar Tudo** | `Esc` | Interrompe imediatamente qualquer ação (Kill Switch). |

> *Nota: Os atalhos podem ser personalizados clicando no botão "Configure Hotkeys" na interface.*

## 🛠️ Instalação e Execução

### Pré-requisitos
Certifique-se de ter o Python 3.10 ou superior instalado.

1. **Clone ou baixe o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/mouse-macro.git](https://github.com/seu-usuario/mouse-macro.git)
   cd mouse-macro
