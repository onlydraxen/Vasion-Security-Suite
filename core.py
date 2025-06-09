# --- START OF FILE core.py ---

import os
import sys
import json
import time
import datetime
import socket
import ctypes
import psutil
import smtplib
import threading
import sqlite3
import platform
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
from ia_perfilador import PerfiladorArchivos

class VasionCore:
    def __init__(self, event_queue, db_path="vasion_intelligence.db", config_path="config.json"):
        print("INICIANDO VasionCore...")
        self.event_queue = event_queue
        
        self.base_path = self._get_base_path()
        self.config_path = os.path.join(self.base_path, config_path)
        self.db_path = os.path.join(self.base_path, db_path)
        self.listas_procesos_path = os.path.join(self.base_path, "listas_procesos.json")
        
        self.config = {}
        self.fernet = None
        self.perfilador_ia = None
        self.lock = threading.Lock()
        self.conn = None
        self.cursor = None
        self.rust_bridge = None

        self._setup_database()
        self._load_core_config()
        self._initialize_ia()
        self._load_rust_bridge()

        self.log_event("VasionCore inicializado con éxito.", component="CORE", event_type="SUCCESS")

    def _get_base_path(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.abspath(os.path.dirname(__file__))

    def _load_core_config(self):
        key_path = os.path.join(self.base_path, "encryption.key")
        try:
            if os.path.exists(key_path):
                with open(key_path, "rb") as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_path, "wb") as f:
                    f.write(key)
            self.fernet = Fernet(key)
        except Exception as e:
            self.log_event(f"Error CRÍTICO al gestionar clave de cifrado: {e}", event_type="CRITICAL")
            raise

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                self.log_event(f"Error CRÍTICO al cargar config.json: {e}", event_type="CRITICAL")
                raise
        else:
            self.log_event("config.json no encontrado. Operando con valores por defecto.", event_type="WARNING")

    def _setup_database(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS eventos (
                                   id INTEGER PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                   tipo_evento TEXT NOT NULL, componente TEXT NOT NULL, mensaje TEXT NOT NULL)''')
            self.conn.commit()
            print("[DB] Base de datos de inteligencia lista.")
        except sqlite3.Error as e:
            print(f"Error CRÍTICO de base de datos: {e}")
            raise

    def _initialize_ia(self):
        api_key = self.config.get("VIRUSTOTAL_API_KEY")
        try:
            self.perfilador_ia = PerfiladorArchivos(virustotal_api_key=api_key)
            self.log_event("IA Perfiladora inicializada.", component="IA_PROFILER", event_type="SUCCESS")
        except Exception as e:
            self.log_event(f"Error al inicializar la IA Perfiladora: {e}", component="IA_PROFILER", event_type="ERROR")
            self.perfilador_ia = None

    def _load_rust_bridge(self):
        self.log_event("Intentando cargar VasionBridge (Rust)...", component="RUST_BRIDGE")
        try:
            if platform.system() == "Windows":
                lib_name = "vasion_bridge.dll"
            else:
                lib_name = "libvasion_bridge.so"
            
            lib_path = os.path.join(self.base_path, 'connectors', 'vasion_bridge', 'target', 'release', lib_name)
            
            if not os.path.exists(lib_path):
                self.log_event(f"No se encontró la librería de Rust en '{lib_path}'. Módulo no disponible.", event_type="WARNING", component="RUST_BRIDGE")
                self.rust_bridge = None
                return
            
            self.rust_bridge = ctypes.CDLL(lib_path)
            
            self.rust_bridge.get_bridge_status.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self.rust_bridge.get_bridge_status.restype = ctypes.c_int

            self.log_event("VasionBridge (Rust) cargado y configurado con éxito.", component="RUST_BRIDGE", event_type="SUCCESS")
        
        except Exception as e:
            self.log_event(f"Error crítico al cargar VasionBridge (Rust): {e}", event_type="CRITICAL", component="RUST_BRIDGE")
            self.rust_bridge = None

    def log_event(self, message, event_type="INFO", component="CORE"):
        log_message = f"[{time.strftime('%H:%M:%S')}] [{component}] [{event_type}] {message}"
        print(log_message)
        
        if self.event_queue:
            event_data = {
                "message": message,
                "event_type": event_type,
                "component": component
            }
            self.event_queue.put(event_data)

        if self.cursor and self.conn:
            try:
                with self.lock:
                    self.cursor.execute(
                        "INSERT INTO eventos (tipo_evento, componente, mensaje) VALUES (?, ?, ?)",
                        (event_type, component, message)
                    )
                    self.conn.commit()
            except sqlite3.Error as e:
                print(f"Error al registrar evento en la base de datos: {e}")

    def start_monitoring_loop(self):
        self.log_event("Iniciando bucle de monitoreo de procesos...", component="MONITOR")
        def loop():
            while True:
                time.sleep(15)
        monitor_thread = threading.Thread(target=loop, daemon=True)
        monitor_thread.start()
        self.log_event("Hilo de monitoreo de procesos en ejecución.", component="MONITOR")

    # --- FUNCIÓN AÑADIDA ---
    def obtener_lista_procesos(self):
        """
        Recopila una lista de los procesos en ejecución con detalles relevantes.
        Devuelve una lista de tuplas.
        """
        self.log_event("Recopilando lista de procesos del sistema...", component="PROCESS_SCAN")
        lista_de_procesos = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_info']):
                try:
                    mem_info = proc.info['memory_info']
                    memoria_mb = f"{mem_info.rss / (1024 * 1024):.1f} MB" if mem_info else "N/A"
                    
                    proc_data = (
                        proc.info['pid'],
                        proc.info['name'] if proc.info['name'] else 'N/A',
                        proc.info['username'] if proc.info['username'] else 'N/A',
                        proc.info['status'] if proc.info['status'] else 'N/A',
                        f"{proc.info['cpu_percent']:.1f}" if proc.info['cpu_percent'] is not None else '0.0',
                        memoria_mb
                    )
                    lista_de_procesos.append(proc_data)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            self.log_event(f"Error al obtener la lista de procesos: {e}", component="PROCESS_SCAN", event_type="ERROR")
        
        self.log_event(f"Se encontraron {len(lista_de_procesos)} procesos.", component="PROCESS_SCAN", event_type="SUCCESS")
        return lista_de_procesos
    # --- FIN DE LA FUNCIÓN AÑADIDA ---

    def cargar_listas_procesos(self):
        """Carga las listas de procesos desde el archivo JSON."""
        try:
            if os.path.exists(self.listas_procesos_path):
                with open(self.listas_procesos_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # Si el archivo no existe, crea uno por defecto
                default_lists = {"whitelist": [], "blacklist": ["regedit.exe", "taskmgr.exe", "wmic.exe"]}
                self.guardar_listas_procesos(default_lists)
                return default_lists
        except (json.JSONDecodeError, IOError) as e:
            self.log_event(f"Error cargando listas de procesos: {e}. Usando valores por defecto.", "ERROR", "LIST_MGMT")
            return {"whitelist": [], "blacklist": []}

    def guardar_listas_procesos(self, listas):
        """Guarda el diccionario de listas en el archivo JSON."""
        try:
            with open(self.listas_procesos_path, "w", encoding="utf-8") as f:
                json.dump(listas, f, indent=4)
            self.log_event("Listas de procesos guardadas correctamente.", "SUCCESS", "LIST_MGMT")
            return True
        except IOError as e:
            self.log_event(f"Error guardando listas de procesos: {e}", "ERROR", "LIST_MGMT")
            return False

    def agregar_a_lista(self, nombre_lista, proceso):
        """Agrega un proceso a la lista especificada (whitelist o blacklist)."""
        if not proceso:
            return False
        proceso = proceso.lower().strip()
        listas = self.cargar_listas_procesos()
        
        if proceso not in listas.get(nombre_lista, []):
            listas.get(nombre_lista, []).append(proceso)
            if self.guardar_listas_procesos(listas):
                self.log_event(f"Proceso '{proceso}' añadido a {nombre_lista}.", "INFO", "LIST_MGMT")
                return True
        return False

    def eliminar_de_lista(self, nombre_lista, proceso):
        """Elimina un proceso de la lista especificada."""
        if not proceso:
            return False
        proceso = proceso.lower().strip()
        listas = self.cargar_listas_procesos()
        
        if proceso in listas.get(nombre_lista, []):
            listas[nombre_lista].remove(proceso)
            if self.guardar_listas_procesos(listas):
                self.log_event(f"Proceso '{proceso}' eliminado de {nombre_lista}.", "INFO", "LIST_MGMT")
                return True
        return False

    def escanear_directorio_completo(self, directorio, callback_gui):
        self.log_event(f"Iniciando escaneo profundo en '{directorio}'...", component="SCANNER", event_type="INFO")
        
        archivos_procesados = 0
        anomalias_encontradas = 0

        if not self.perfilador_ia:
            self.log_event("El módulo de IA no está disponible. Abortando escaneo.", component="SCANNER", event_type="ERROR")
            if callback_gui: callback_gui({"procesados": 0, "anomalias": 0})
            return

        try:
            for root, _, files in os.walk(directorio):
                for file in files:
                    ruta_completa = os.path.join(root, file)
                    if not os.path.isfile(ruta_completa): continue
                    
                    try:
                        self.perfilador_ia.registrar_actividad_archivo(ruta_completa)
                        es_anomalo, razon = self.perfilador_ia.es_anomalo(ruta_completa)
                        
                        if es_anomalo:
                            anomalias_encontradas += 1
                            self.log_event(f"¡ANOMALÍA! Archivo: {os.path.basename(ruta_completa)}. Razón: {razon}", component="IA_SCAN", event_type="CRITICAL")

                        archivos_procesados += 1
                        if archivos_procesados % 100 == 0:
                            self.log_event(f"{archivos_procesados} archivos escaneados...", component="SCANNER", event_type="INFO")
                    
                    except Exception as e:
                        self.log_event(f"No se pudo procesar el archivo {os.path.basename(ruta_completa)}: {e}", component="SCANNER", event_type="WARNING")

        except Exception as e:
            self.log_event(f"Error crítico durante el escaneo del directorio {directorio}: {e}", component="SCANNER", event_type="CRITICAL")

        resultado_final = {"procesados": archivos_procesados, "anomalias": anomalias_encontradas}
        self.log_event(f"Escaneo profundo completado. Archivos: {archivos_procesados}. Anomalías: {anomalias_encontradas}.", component="SCANNER", event_type="SUCCESS")
        
        if callback_gui:
            callback_gui(resultado_final)

    def stop(self):
        if self.conn:
            self.conn.close()
            print("Conexión a la base de datos cerrada.")
        print("VasionCore detenido.")
        
# --- END OF FILE core.py ---