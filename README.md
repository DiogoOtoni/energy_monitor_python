
# Energy Monitor

Aplicativo com interface gráfica (Tkinter) para monitorar o consumo de energia do seu computador, estimar custo e salvar sessões em JSON.

# 1. Comandos para TESTAR o CÓDIGO no Windows e Linux

## Pré-requisitos no Windows:
1. **Instalar Python**:
   - Baixe do site oficial (python.org)
   - Marque a opção "Add Python to PATH"
   - Inclua "tcl/tk and IDLE" na instalação

2. **Sequência de comandos no PowerShell/CMD**:
```powershell
# Navegue até a pasta do projeto
cd C:\Users\SeuNome\pasta\pasta\pasta_do_projeto

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual (no TERMINAL GITBASH)
source venv/Scripts/activate

# Atualize pip
python.exe -m pip install --upgrade pip

# Dependencia de instalação manual primeiro
pip install pythonnet==3.1.0rc0
pip install pywin32

# Instalação das demais dependencias
pip install -r requirements.txt

# Execute o programa
python main.py
```

## Pré-requisitos no Linux:

1. **Sequência de comandos no Terminal**:
```powershell
## Navegue até a pasta do projeto
# (Lembre-se que no Linux o caminho geralmente começa em /home/usuario)
cd ~/Documents/energy_monitor

# Crie um ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Execute o programa
python3 main.py
```

## 2. **Tkinter (biblioteca GUI do Python)**  
   Tkinter vem junto com a instalação do Python no Windows e no macOS.  
   No Linux, a instalação varia conforme a distribuição:

   **Ubuntu / Debian**
   ```bash
   sudo apt update
   sudo apt install python3 python3-tk python3-venv
   ```

   **Fedora**
   ```bash
   sudo dnf install python3 python3-tkinter
   ```

   **Arch Linux**
   ```bash
   sudo pacman -S python tk
   ```

# 2. Transformar em instalável para distribuição

## A. Para Linux (.deb para Ubuntu/Debian)

### Usando PyInstaller:

- Certifique-se de que o Tk está instalado (veja comandos acima).
  - Se receber erro de execução (arquitetura, dependências), use:
    ```bash
    sudo apt install libx11-6 libxext6 libxcb1 libxfixes3 libxi6
    ```
  - marque o arquivo como executável:
    ```bash
    chmod +x EnergyMonitor
    ```

```bash
# Instale o PyInstaller
pip install pyinstaller

# Crie o executável
pyinstaller --onefile --windowed --name "EnergyMonitor" main.py

# O executável estará em dist/EnergyMonitor
# Para criar um ícone, pode usar uma imagem .png e converter para .ico
# Para ícone, adicionar no comando pyinstaller: --icon=icone.ico --add-data "icone.ico:."
```

## B. Para Windows (.exe)

### Usando PyInstaller:

- Certifique-se de ter o *Microsoft Visual C++ Redistributable 2015–2022* instalado:
    https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist
  - Em alguns antivírus, pode ser necessário liberar o executável manualmente.

```powershell
# No ambiente virtual com PyInstaller instalado
pyinstaller --onefile --windowed --name "EnergyMonitor.exe" main.py

# O executável estará em dist\EnergyMonitor.exe
# Para ícone, adicionar no comando pyinstaller: --icon=icone.ico
```


## C. Para macOS (.app)
```bash
# No macOS com PyInstaller
pip install pyinstaller

# Crie o .app
pyinstaller --windowed --name "Energy Monitor" --icon=icone.icns main.py

# O .app estará em dist/Energy Monitor.app
```

- Ao abrir pela primeira vez, pode aparecer o alerta “Aplicativo baixado da internet”.
- Vá em “Preferências do Sistema → Segurança e Privacidade → Geral” e libere o app.
- Não é necessário instalar Python separadamente (o .app já inclui a runtime).

---

## 🛠️ Solução de Problemas (Troubleshooting)

### Erro: `ModuleNotFoundError: No module named 'tkinter'`
Isso significa que o Python não instalou os componentes gráficos.
- **Windows**: Reinstale o Python e marque a opção "tcl/tk and IDLE".
- **Linux**: Rode `sudo apt-get install python3-tk`.

### Erro: `ModuleNotFoundError: No module named 'psutil'`
Você esqueceu de rodar o comando `pip install -r requirements.txt`.

### O programa não mede minha placa de vídeo (GPU)
A biblioteca `GPUtil` suporta apenas placas de vídeo da NVIDIA. Se você usa AMD ou Intel, o medidor de GPU aparecerá como 0 ou o programa usará apenas o consumo geral da CPU/Motherboard.

### O programa mostra valores negativos
Se isso ocorrer, verifique se você está rodando a versão mais recente do código, pois adotamos proteções contra esse bug.

---

## 📜 Licença
Este software é livre para uso pessoal.