# 🖱️ Macro Recorder com Interface Gráfica

Este é um gravador e reprodutor de macros para mouse e teclado desenvolvido em Python, com interface gráfica baseada em Tkinter. Ele permite automatizar tarefas repetitivas no seu computador com facilidade.

## 🚀 Funcionalidades

- Gravação de eventos do mouse e teclado.
- Execução automática das ações gravadas com delays preservados.
- Interface gráfica amigável.
- Suporte a múltiplos ciclos de repetição.
- Salvamento e carregamento de arquivos `.json` contendo as macros.
- Atalhos configuráveis para gravação, reprodução e parada.

## 🎮 Atalhos padrão

| Ação             | Atalho padrão |
|------------------|---------------|
| Iniciar Execução | `Ctrl+1`      |
| Iniciar Gravação | `Ctrl+3`      |
| Parar Tudo       | `Esc`         |

Os atalhos podem ser alterados na interface gráfica.

## 📂 Estrutura de Arquivos

- As macros gravadas são salvas automaticamente na pasta `macros/` no mesmo diretório do script.
- Cada macro é salva como um arquivo `.json` com os dados de resolução e ações.

## 🛠️ Requisitos

- Python 3.8 ou superior
- Bibliotecas Python:
  - `pynput`
  - `keyboard`
  - `pyautogui`
  - `tkinter` (incluso no Python)
  
Instale as dependências com:

```bash
pip install pynput keyboard pyautogui
