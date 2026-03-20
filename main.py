import json
from json import JSONDecodeError
import os
import time
import threading
import datetime
import platform
import subprocess
import psutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox



if platform.system() == "Windows":
    import wmi

CONFIG_FILE = "config.json"
SESSIONS_FILE = "energy_monitor_sessions.json"

def ensure_sessions_file():
    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'w') as f:
            json.dump({'sessions': []}, f, indent=2)
    else:
        try:
            with open(SESSIONS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    raise JSONDecodeError("empty", content, 0)
                data = json.loads(content)
                if not isinstance(data, dict) or 'sessions' not in data:
                    raise JSONDecodeError("bad format", content, 0)
        except JSONDecodeError:
            with open(SESSIONS_FILE, 'w') as f:
                json.dump({'sessions': []}, f, indent=2)

ensure_sessions_file()

def load_sessions():
    try:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    except (JSONDecodeError, FileNotFoundError):
        return {'sessions': []}

def save_sessions(data):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class EnergyMonitor:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.current_session_id = None
        self.kwh_price = 0.0
        self.running = True
        self.total_energy_wh = 0.0
        self.last_energy_uj = None # para RAPL em linux
        self.last_measurement_time = None
        self.current_power = 0.0

        self.last_hourly_save = datetime.datetime.now()

        self.energy_at_last_save = 0.0

        #carregar config
        self.load_config()

        #iniciar nova sessão
        self.start_new_session()

        #configurar GUI
        self.setup_gui()

        #iniciar thread de monitoramento
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.kwh_price = config.get('kwh_price', 0.0)
        else:
            self.kwh_price = 0.0
            self.save_config()
    
    def save_config(self):
        config = {'kwh_price': self.kwh_price}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def start_new_session(self):
        session = {
            'id': self.get_next_session_id(),
            'start_time': self.start_time.isoformat(),
            'end_time': None,
            'total_kwh': 0.0,
            'cost': 0.0,
            'kwh_price': self.kwh_price
        }
        self.current_session_id = session['id']
        self.add_session(session)
    
    def get_next_session_id(self):
        data = load_sessions()
        sessions = data.get('sessions', [])
        if sessions:
            return max(s['id'] for s in sessions) + 1
        return 1

    def add_session(self, session):
        data = load_sessions()
        data['sessions'].append(session)
        save_sessions(data)
    
    def update_session(self, session_id, updates):
        data = load_sessions()
        for session in data['sessions']:
            if session['id'] == session_id:
                if 'measurements' in updates:
                    session.setdefault('measurements', []).append(updates['measurements'])
                
                for k, v in updates.items():
                    if k != 'measurements':
                        session[k] = v
                break
        save_sessions(data)
    
    def get_system_power_usage(self):
        current_time = time.time()

        if platform.system() == "Linux":
            return self.get_linux_power_usage(current_time)
        elif platform.system() == "Windows":
            return self.get_windows_power_usage()
        elif platform.system() == "Darwin":
            return self.get_macos_power_usage()
        else:
            return self.get_fallback_power_estimate()
    
        
    def get_linux_power_usage(self, current_time):
        """Medição real de energia no linux usando RAPL
            Verifica suporte ao RAPL
            ler contador de energia
            faz primeira medição
            calcula potencia
            atualiza valores
            retorna
        """
        try:
            rapl_path = '/sys/class/powercap/intel-rapl'
            if not os.path.exists(rapl_path):
                return self.get_fallback_power_estimate()
            
            domain_path = os.path.join(rapl_path, 'intel-rapl:0')
            energy_uj_file = os.path.join(domain_path, 'energy_uj')

            if not os.path.exists(energy_uj_file):
                return self.get_fallback_power_estimate()

            with open(energy_uj_file, 'r') as f:
                current_energy_uj = int(f.read())
            
            now = time.time()

            # =================================================================
            # VERIFICAÇÃO DE SEGURANÇA (Previne o erro float - None)
            # =================================================================
            # Se for a primeira execução ou as variáveis forem None,
            # apenas definimos os valores iniciais e retornamos 0.
            if self.last_energy_uj is None or self.last_measurement_time is None:
                print("Inicializando sensores RAPL...")
                self.last_energy_uj = current_energy_uj
                self.last_measurement_time = now
                return 0.0

            # Calcula a diferença de tempo desde a última leitura
            time_diff = now - self.last_measurement_time
            
            # Evita divisão por zero (caso o loop rode muito rápido)
            if time_diff <= 0:
                time_diff = 0.001

            # Calcula a diferença de energia
            energy_diff_uj = current_energy_uj - self.last_energy_uj

            # =================================================================
            # PROTEÇÃO CONTRA WRAP-AROUND (Sensor zerou)
            # =================================================================
            # Se a diferença for negativa (sensor voltou para zero) ou absurda,
            # ignoramos essa leitura para evitar valores negativos.
            if energy_diff_uj < 0 or energy_diff_uj > (time_diff * 1e6 * 100000):
                print("Aviso: Wrap-around do sensor RAPL ou valor anômalo detectado.")
                # Atualiza a referência de energia para a nova leitura atual
                # mas zera o timer para evitar picos de potência na próxima leitura
                self.last_energy_uj = current_energy_uj
                self.last_measurement_time = now
                return 0.0

            # Converte para Watts: (microjoules / (segundos * 1.000.000))
            power_watts = energy_diff_uj / (time_diff * 1e6)

            # Atualiza referências para o próximo ciclo
            self.last_energy_uj = current_energy_uj
            self.last_measurement_time = now

            return power_watts
        
        except PermissionError as e:
            print(f"Acesso negado a RAPL (precisa de sudo?): {e}")
            return self.get_fallback_power_estimate()
        except Exception as e:
            print(f"Erro na medição RAPL: {e}")
            return self.get_fallback_power_estimate()

    
    def get_windows_power_usage(self):
        """
            Medição real de energia no windows usando WMI
            CPU
            GPU
            Outros componentes
        """
        try:
            import wmi
            c = wmi.WMI()
            total_power = 0.0

            for cpu in c.Win32_Processor():
                if hasattr(cpu, 'CurrentClockSpeed'):
                    freq_ghz = cpu.CurrentClockSpeed / 1000

                    cpu_power = 5 + (freq_ghz * 10)
                    total_power += cpu_power

            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=power.draw', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    gpu_power = float(result.stdout.strip())
                    total_power += gpu_power
            except:
                pass

            total_power += 15.0
            return total_power

        except Exception as e:
            print(f"Erro na medição WMI: {e}")
            return self.get_fallback_power_estimate()
    
    def get_macos_power_usage(self):
        """
        Medição real de energia no macOS usando powermetrics

        """
        try:
            cmd = [
                'powermetrics', '--samplers', 'power', '--show', 'all', '--json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)

            if result.returncode == 0:
                data = json.loads(result.stdout)

                if 'system_power' in data:
                    return data['system_power']
            
            return self.get_fallback_power_estimate()
        
        except Exception as e:
            print(f"Erro na medição macOS: {e}")
            return self.get_fallback_power_estimate()
    
    def get_fallback_power_estimate(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        base_power = 30.0
        cpu_power = (cpu_percent / 100) * 70.0
        memory_power = (memory.percent / 100) * 10.0

        return base_power + cpu_power + memory_power

    def monitoring_loop(self):
        """
        Loop principal de monitoramento
        """
        while self.running:
            try:
                # mede consumo atual
                self.current_power = self.get_system_power_usage()

                # Acumula energia (Wh) = Potência (W) × tempo (h)
                # Como medimos a cada 1 segundo: tempo = 1/3600 h
                self.total_energy_wh += self.current_power * (1/3600)

                # Verifica se já passou 1 hora desde o último salvamento
                now = datetime.datetime.now()

                if (now - self.last_hourly_save).total_seconds() >= 3600:
                    hourly_energy = self.total_energy_wh - self.energy_at_last_save
                
                    # Opcional: Calcular custo apenas desta hora
                    hourly_cost = (hourly_energy / 1000.0) * self.kwh_price

                    # Registra medição horária
                    measurement = {
                        'timestamp': self.last_hourly_save.isoformat(),
                        'power_watts': self.current_power,
                        'energy_wh': hourly_energy,
                        'cost_hour': round(hourly_cost, 4)
                    }
                    
                    self.update_session(self.current_session_id, {'measurements': measurement})


                    self.last_hourly_save = now
                    self.energy_at_last_save = self.total_energy_wh

                self.root.after(0, self.update_gui)

                time.sleep(1)
            except Exception as e:
                print(f"Erro no loop de monitoramento: {e}")
                time.sleep(1)
    
    def get_previous_energy(self):
        """Retorna o último energy_wh salvo no JSON"""
        data = load_sessions()
        for session in data['sessions']:
            if session['id'] == self.current_session_id:
                measurements = session.get('measurements', [])
                if measurements:
                    return measurements[-1]['energy_wh']
        return 0.0
    
    def update_gui(self):
        elapsed = datetime.datetime.now() - self.start_time
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        energy_kwh = self.total_energy_wh / 1000.0
        cost = energy_kwh * self.kwh_price

        self.time_label.config(text=f"Tempo {int(hours): 02d}:{int(minutes):02d}:{int(seconds):02d}")
        self.power_label.config(text=f"Potencia: {self.current_power:.1f} W")
        self.energy_label.config(text=f"Energia: {energy_kwh:.4f} KWh")
        self.cost_label.config(text=f"Custo: R$ {cost:.4f}")

        progress = min((elapsed.total_seconds() / 3600) * 100, 100)
        self.progress_bar['value'] = progress
    
    def setup_gui(self):
        

        self.root = tk.Tk()
        self.root.title("Energy Monitor - medicao real")
        self.root.geometry("450x350")
        self.root.resizable(False, False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        system_info = f"Sistema: {platform.system()} | Método: {self.get_measurement_method()}"
        ttk.Label(main_frame, text=system_info, font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)

        ttk.Label(main_frame, text="Preço do kWh (R$): ").grid(row=1, column=0, sticky=tk.W)
        self.price_entry = ttk.Entry(main_frame, width=10)
        self.price_entry.insert(0, str(self.kwh_price))
        self.price_entry.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Button(main_frame, text="Salvar", command=self.save_price).grid(row=1, column=2, padx=5)

        #Labels de informação
        self.time_label = ttk.Label(main_frame, text="Tempo: 00:00:00", font=('Arial', 10))
        self.time_label.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.power_label = ttk.Label(main_frame, text="Potência: 0.0 W", font=('Arial', 10))
        self.power_label.grid(row=3, column=0, columnspan=3, pady=5)
        
        self.energy_label = ttk.Label(main_frame, text="Energia: 0.0000 kWh", font=('Arial', 10))
        self.energy_label.grid(row=4, column=0, columnspan=3, pady=5)
        
        self.cost_label = ttk.Label(main_frame, text="Custo: R$ 0.0000", font=('Arial', 10))
        self.cost_label.grid(row=5, column=0, columnspan=3, pady=5)

        # Barra de progresso
        self.progress_bar = ttk.Progressbar(main_frame, length=350, mode='determinate')
        self.progress_bar.grid(row=6, column=0, columnspan=3, pady=20)
        
        # Informações adicionais
        info_text = "Monitorando consumo de energia em tempo real"
        ttk.Label(main_frame, text=info_text, font=('Arial', 9, 'italic')).grid(row=7, column=0, columnspan=3)

    def get_measurement_method(self):
        """Retorna o método de medição atual"""
        if platform.system() == "Linux":
            return "RAPL (Intel)"
        elif platform.system() == "Windows":
            return "WMI + NVIDIA"
        elif platform.system() == "Darwin":
            return "powermetrics"
        else:
            return "Estimativa"
    
    def save_price(self):
        """Salva o novo preço do kWh"""
        try:
            new_price = float(self.price_entry.get())
            self.kwh_price = new_price
            self.save_config()
            messagebox.showinfo("Sucesso", "Preço atualizado!")
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido!")
    
    def on_closing(self):
        """Ao fechar a janela"""
        self.running = False
        
        # Salva última medição (mesmo que hora não tenha completado)
        now = datetime.datetime.now()

        partial_consumption = self.total_energy_wh - self.energy_at_last_save

        measurement = {
            'timestamp': self.last_hourly_save.isoformat(),
            'power_watts': self.current_power,
            'energy_wh': partial_consumption
        }
        self.update_session(self.current_session_id, {'measurements': measurement})

        final_kwh = self.total_energy_wh / 1000.0
        final_cost = final_kwh * self.kwh_price

        # Finaliza a sessão
        self.update_session(self.current_session_id, {
            'end_time': now.isoformat(),
            'total_kwh': final_kwh,
            'cost': final_cost
        })

        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EnergyMonitor()
    
    app.run()

   
    
