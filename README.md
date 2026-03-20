
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

# Ative o ambiente virtual
venv\Scripts\activate

# Instale as dependências
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

# 2. Transformar em instalável para distribuição

## A. Para Linux (.deb para Ubuntu/Debian)

### Usando PyInstaller:
```bash
# Instale o PyInstaller
pip install pyinstaller

# Crie o executável
pyinstaller --onefile --windowed --name "EnergyMonitor" --icon=icone.ico --add-data "icone.ico:." main.py

# O executável estará em dist/EnergyMonitor
# Para criar um ícone, pode usar uma imagem .png e converter para .ico
```

## B. Para Windows (.exe)

### Usando PyInstaller:
```powershell
# No ambiente virtual com PyInstaller instalado
pyinstaller --onefile --windowed --name "EnergyMonitor.exe" --icon=icone.ico main.py

# O executável estará em dist\EnergyMonitor.exe
```


## C. Para macOS (.app)
```bash
# No macOS com PyInstaller
pip install pyinstaller

# Crie o .app
pyinstaller --windowed --name "Energy Monitor" --icon=icone.icns main.py

# O .app estará em dist/Energy Monitor.app
```
