import os
import json
import time
from collections import defaultdict
import threading
import datetime
import math
import hashlib
import socket  
import requests
import ctypes

# Importaciones para Machine Learning
from sklearn.ensemble import IsolationForest
import numpy as np # Para manejo de arrays numéricos
import joblib # Para cargar/guardar el modelo de ML

DLL_NAME = "db_module.dll"
DLL_PATH = os.path.join(os.path.dirname(__file__), DLL_NAME)
db_dll = None

try:
    # Carga la biblioteca compartida (DLL)
    db_dll = ctypes.CDLL(DLL_PATH)

    # Define el tipo de argumento de la función C++ que vamos a llamar.
    # 'c_char_p' es para una cadena de caracteres (char* en C++).
    db_dll.guardar_registro_c.argtypes = [ctypes.c_char_p]

    # Define el tipo de retorno de la función C++.
    # 'None' porque nuestra función C++ 'void guardar_registro_c' no devuelve nada.
    db_dll.guardar_registro_c.restype = None

    print(f"[{time.strftime('%H:%M:%S')}] Carga de DLL C++ '{DLL_NAME}' exitosa.")

except OSError as e:
    print(f"[{time.strftime('%H:%M:%S')}] ERROR: No se pudo cargar la DLL C++ '{DLL_NAME}'. {e}")
    print("Asegúrate de que 'db_module.dll' esté en la misma carpeta que este script, o que la ruta sea correcta.")
    # Opcional: si la DLL es crítica, podrías salir del programa o deshabilitar la funcionalidad.
    db_dll = None # Asegúrate de que la variable sea None si falla la carga.

# --- Función de envoltura para llamar al C++ desde Python ---
def registrar_dato_en_c(dato_str):
    if db_dll:
        try:
            # Codifica la cadena de Python (Unicode) a bytes (UTF-8)
            # porque C++ espera un char* (secuencia de bytes).
            db_dll.guardar_registro_c(dato_str.encode('utf-8'))
            # print(f"Dato '{dato_str}' enviado a módulo C++.") # Puedes descomentar para depurar
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ERROR al llamar a la función C++ 'guardar_registro_c': {e}")
    else:
        # print("Módulo C++ no cargado. No se pudo registrar el dato.") # Puedes descomentar para depurar
        pass # No hace nada si la DLL no se cargó

class PerfiladorArchivos:
    def __init__(self, perfil_path="perfil_archivos_ia.json", model_path="ia_modelo_forest.joblib", virustotal_api_key=None):
        """
        Inicializa el perfilador de archivos con IA y VirusTotal.
        Carga el perfil existente o crea uno nuevo si no existe.
        """
        self.perfil_path = perfil_path
        self.model_path = model_path
        self.virustotal_api_key = virustotal_api_key
        self.lock = threading.Lock() # Para asegurar la seguridad de hilos al acceder al perfil

        # Parámetros para el entrenamiento de la IA
        self.aprendizaje_min_archivos = 100 # Mínimo de archivos antes de que la IA empiece a alertar/entrenar
                                          # Reducido para pruebas, puedes subirlo a 1000
        self.reentrenamiento_intervalo = 50 # Reentrenar cada X archivos procesados
                                          # Reducido para pruebas, puedes subirlo a 500

        # Estructura del perfil (se cargará o inicializará)
        self.perfil = {
            "total_files_processed": 0,
            "last_trained_count": 0,
            "extension_data": defaultdict(lambda: {"count": 0, "last_seen": None, "locations": defaultdict(int)}),
            "location_data": defaultdict(lambda: defaultdict(lambda: {"count": 0, "last_seen": None})),
            "data_for_training": [], # Almacenará las características de los archivos para el entrenamiento
            "vt_cache": {} # Caché para resultados de VirusTotal por hash
        }
        self.model = None # El modelo de Isolation Forest

        # Cargar el perfil existente y el modelo
        self._cargar_perfil()
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("IA: Modelo de Isolation Forest cargado correctamente.")
            except Exception as e:
                print(f"IA: Error al cargar el modelo: {e}. Se entrenará uno nuevo cuando haya suficientes datos.")
                self.model = None

        # Extensiones de archivos considerados "ejecutables" o de riesgo (para características adicionales si se usan)
        self.ejecutables_sospechosos = [".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".scr", ".pif", ".dll", ".com"]
        self.system_config_extensions = [".sys", ".ini", ".conf", ".dat", ".reg", ".dll", ".so", ".dylib"] # Archivos de configuración/sistema
        
        # Diccionario para mapear extensiones a un valor numérico si se usa como característica
        self.extension_to_numeric = self._generar_mapeo_extensiones()


    def _generar_mapeo_extensiones(self):
        """Genera un mapeo numérico para un conjunto fijo de extensiones, útil para características."""
        mapeo = {}
        # Un valor para extensiones comunes/seguras
        mapeo["_default_"] = 0 
        
        # Valores para ejecutables/sospechosos
        for ext in self.ejecutables_sospechosos:
            mapeo[ext] = 1
        
        # Valores para archivos de sistema/configuración
        for ext in self.system_config_extensions:
            if ext not in mapeo: # Evitar sobrescribir si ya está en sospechosos
                mapeo[ext] = 2

        # Otros tipos de archivos que podrías querer categorizar:
        # mapeo[".doc"] = 3
        # mapeo[".pdf"] = 4
        # ...
        return mapeo

    def _get_numeric_extension(self, extension):
        """Devuelve el valor numérico para una extensión."""
        return self.extension_to_numeric.get(extension, self.extension_to_numeric["_default_"])

    def _cargar_perfil(self):
        """Carga el perfil de actividad desde el archivo JSON."""
        if os.path.exists(self.perfil_path):
            try:
                with open(self.perfil_path, 'r', encoding='utf-8') as f:
                    cargado = json.load(f)
                    # Restaurar defaultdicts
                    self.perfil["extension_data"] = defaultdict(lambda: {"count": 0, "last_seen": None, "locations": defaultdict(int)}, cargado.get("extension_data", {}))
                    # La carga de location_data es más compleja debido a su anidamiento
                    self.perfil["location_data"] = defaultdict(lambda: defaultdict(lambda: {"count": 0, "last_seen": None}))
                    for loc, ext_data in cargado.get("location_data", {}).items():
                        for ext, data in ext_data.items():
                            self.perfil["location_data"][loc][ext] = defaultdict(int, data) # Asume que 'count' y 'last_seen' están aquí
                    
                    self.perfil["total_files_processed"] = cargado.get("total_files_processed", 0)
                    self.perfil["last_trained_count"] = cargado.get("last_trained_count", 0)
                    self.perfil["data_for_training"] = cargado.get("data_for_training", [])
                    self.perfil["vt_cache"] = cargado.get("vt_cache", {})
                print(f"IA: Perfil cargado desde {self.perfil_path}. Archivos procesados: {self.perfil['total_files_processed']}")
            except json.JSONDecodeError:
                print(f"IA: Error: El archivo de perfil '{self.perfil_path}' está corrupto. Se creará uno nuevo.")
            except Exception as e:
                print(f"IA: Error al cargar el perfil '{self.perfil_path}': {e}. Se creará uno nuevo.")

    def _guardar_perfil(self):
        """Guarda el perfil de actividad en el archivo JSON."""
        with self.lock:
            # Convertir defaultdicts a dict para JSON antes de guardar
            perfil_para_guardar = {
                "total_files_processed": self.perfil["total_files_processed"],
                "last_trained_count": self.perfil["last_trained_count"],
                "extension_data": {ext: {k: v if not isinstance(v, defaultdict) else dict(v) for k, v in data.items()} for ext, data in self.perfil["extension_data"].items()},
                "location_data": {loc: {ext: dict(data) for ext, data in ext_data.items()} for loc, ext_data in self.perfil["location_data"].items()},
                "data_for_training": self.perfil["data_for_training"],
                "vt_cache": self.perfil["vt_cache"]
            }
            try:
                with open(self.perfil_path, 'w', encoding='utf-8') as f:
                    json.dump(perfil_para_guardar, f, indent=4)
                #print(f"IA: Perfil guardado en {self.perfil_path}.")
            except Exception as e:
                print(f"IA: Error al guardar el perfil en {self.perfil_path}: {e}")

    def calculate_file_hash(self, file_path, hash_algorithm='sha256'):
        """Calcula el hash de un archivo."""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise FileNotFoundError(f"Archivo no encontrado o no es un archivo: {file_path}")

        hasher = hashlib.sha256() if hash_algorithm == 'sha256' else hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"IA: Error al calcular el hash de {file_path}: {e}")
            return None

    def _escanear_virustotal(self, file_hash):
        """
        Consulta la API de VirusTotal para un hash de archivo.
        Implementa un caché simple para no consultar repetidamente.
        """
        if not self.virustotal_api_key:
            print("IA: No hay clave API de VirusTotal configurada.")
            return None

        if file_hash in self.perfil["vt_cache"]:
            # print(f"IA: Hash {file_hash} encontrado en caché de VirusTotal.")
            return self.perfil["vt_cache"][file_hash]

        # Comprobar conectividad a internet antes de la consulta
        try:
            socket.create_connection(("www.google.com", 80), timeout=5)
        except OSError:
            print("IA: No hay conexión a internet para VirusTotal.")
            return None

        url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers = {
            "x-apikey": self.virustotal_api_key
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Lanza una excepción para códigos de estado de error (4xx o 5xx)
            data = response.json()
            
            # Procesar la respuesta
            if 'data' in data and 'attributes' in data['data']:
                attributes = data['data']['attributes']
                # VT_API_V3_REVISADO
                last_analysis_stats = attributes.get('last_analysis_stats', {})
                positives = last_analysis_stats.get('malicious', 0) + last_analysis_stats.get('suspicious', 0)
                total = last_analysis_stats.get('harmless', 0) + last_analysis_stats.get('malicious', 0) + last_analysis_stats.get('suspicious', 0) + last_analysis_stats.get('undetected', 0) + last_analysis_stats.get('timeout', 0)

                report = {
                    "positives": positives,
                    "total": total,
                    "last_analysis_date": attributes.get('last_analysis_date')
                }
                self.perfil["vt_cache"][file_hash] = report
                # print(f"IA: Reporte de VirusTotal para {file_hash}: Positivos={positives}, Total={total}")
                return report
            else:
                print(f"IA: No se encontraron datos para el hash {file_hash} en VirusTotal.")
                self.perfil["vt_cache"][file_hash] = None # Almacenar como None para no volver a consultar
                return None
        except requests.exceptions.RequestException as e:
            print(f"IA: Error en la consulta a VirusTotal para {file_hash}: {e}")
            if response.status_code == 429: # Límite de tasa excedido
                print("IA: Límite de tasa de VirusTotal excedido. Intenta de nuevo más tarde.")
            return None
        except Exception as e:
            print(f"IA: Error inesperado al procesar respuesta de VirusTotal para {file_hash}: {e}")
            return None

    def _obtener_caracteristicas_archivo(self, ruta_archivo, virustotal_positives=0, virustotal_total=0, es_sospechoso_fijo=False):
        """
        Recopila características numéricas de un archivo para el modelo de Machine Learning.
        Estas características incluyen: tamaño, existencia, tiempo de creación/modificación,
        información de VirusTotal y si es sospechoso por cadenas fijas.
        """
        try:
            # Característica 1: Tamaño del archivo en bytes
            tamanio_bytes = os.path.getsize(ruta_archivo)

            # Característica 2: Si el archivo existe (1 para sí, 0 para no)
            existe = 1 if os.path.exists(ruta_archivo) else 0

            # Característica 3 y 4: Antigüedad del archivo en segundos desde su creación/modificación
            tiempo_actual = time.time()
            tiempo_creacion = os.path.getctime(ruta_archivo)
            tiempo_modificacion = os.path.getmtime(ruta_archivo)

            antiguedad_creacion_segundos = tiempo_actual - tiempo_creacion
            antiguedad_modificacion_segundos = tiempo_actual - tiempo_modificacion
            
            # Asegurarse de que los tiempos no sean negativos (puede ocurrir con archivos recién creados o sync)
            if antiguedad_creacion_segundos < 0: antiguedad_creacion_segundos = 0
            if antiguedad_modificacion_segundos < 0: antiguedad_modificacion_segundos = 0

            # Característica 5 y 6: Resultados de VirusTotal (positivos y totales)
            # El modelo puede aprender de los valores brutos.

            # Característica 7: Indicador de si fue marcado como sospechoso por cadenas fijas
            # 1 si es sospechoso, 0 si no lo es
            flag_sospechoso_fijo = 1 if es_sospechoso_fijo else 0

            # Característica 8: Tipo de extensión (numérico)
            extension = os.path.splitext(ruta_archivo)[1].lower()
            extension_numerica = self._get_numeric_extension(extension)

            # Devolver las características como un array numpy
            # ¡IMPORTANTE! El orden y número de características deben ser CONSISTENTES
            # con lo que el modelo de IA fue entrenado o será entrenado.
            return np.array([
                float(tamanio_bytes),
                float(existe),
                float(antiguedad_creacion_segundos),
                float(antiguedad_modificacion_segundos),
                float(virustotal_positives),
                float(virustotal_total),
                float(flag_sospechoso_fijo),
                float(extension_numerica) # Nueva característica
            ], dtype=np.float32) # Usar float32 para compatibilidad con librerías ML

        except FileNotFoundError:
            print(f"IA: Archivo no encontrado al obtener características: {ruta_archivo}")
            return None
        except Exception as e:
            print(f"IA: Error inesperado al obtener características de {ruta_archivo}: {e}")
            return None

    def registrar_actividad_archivo(self, ruta_archivo, es_sospechoso=False):
        """
        Registra la actividad de un archivo y recopila datos para el entrenamiento de la IA.
        Ahora incluye escaneo de VirusTotal y un flag de sospecha para el entrenamiento.
        """
        if not os.path.exists(ruta_archivo) or not os.path.isfile(ruta_archivo):
            return

        extension = os.path.splitext(ruta_archivo)[1].lower()
        directorio = os.path.dirname(ruta_archivo)
        current_time = datetime.datetime.now().isoformat()

        # Bloqueamos el acceso al perfil mientras lo actualizamos para evitar conflictos entre hilos
        with self.lock:
            # Actualizar perfil de actividad general (conteo de extensiones, ubicaciones)
            if extension not in self.perfil["extension_data"]:
                self.perfil["extension_data"][extension] = {"count": 0, "last_seen": None, "locations": defaultdict(int)}
            self.perfil["extension_data"][extension]["count"] += 1
            self.perfil["extension_data"][extension]["last_seen"] = current_time
            self.perfil["extension_data"][extension]["locations"][directorio] += 1

            # Asegurarse de que el diccionario de extensiones exista para la ubicación
            if directorio not in self.perfil["location_data"]:
                self.perfil["location_data"][directorio] = defaultdict(lambda: defaultdict(int))
            if extension not in self.perfil["location_data"][directorio]:
                 self.perfil["location_data"][directorio][extension] = {"count": 0, "last_seen": None}
            self.perfil["location_data"][directorio][extension]["count"] += 1
            self.perfil["location_data"][directorio][extension]["last_seen"] = current_time

            self.perfil["total_files_processed"] += 1

            # --- INICIO DE LA LÓGICA DE HASH Y VIRUSTOTAL ---
            file_hash = None
            try:
                file_hash = self.calculate_file_hash(ruta_archivo)
            except Exception as e:
                print(f"IA: Error al calcular hash de {ruta_archivo}: {e}")
                                        
            vt_positives = 0 # Por defecto, 0 positivos (modo local)
            vt_total = 0     # Por defecto, 0 total de motores (modo local)

            if file_hash and self.virustotal_api_key: # Si tenemos hash y clave API
                vt_report = self._escanear_virustotal(file_hash)
                if vt_report is not None:
                    vt_positives = vt_report.get('positives', 0)
                    vt_total = vt_report.get('total', 0)
                else:
                    print(f"IA: Fallback a modo local para VirusTotal en {ruta_archivo}. Usando 0/0.")
            elif not self.virustotal_api_key:
                print(f"IA: No hay clave API de VirusTotal configurada. Usando 0/0 para VirusTotal en {ruta_archivo}.")
            
            # OBTENER CARACTERÍSTICAS DEL ARCHIVO, PASANDO LOS DATOS RELEVANTES
            caracteristicas = self._obtener_caracteristicas_archivo(
                ruta_archivo,
                virustotal_positives=vt_positives,   # Datos de VirusTotal
                virustotal_total=vt_total,           # Datos de VirusTotal
                es_sospechoso_fijo=es_sospechoso     # Indicador de sospecha por cadenas fijas de Vasion
            )

            if caracteristicas is not None:
                self.perfil["data_for_training"].append(caracteristicas.tolist()) # Convertir numpy array a lista para JSON

                ### AÑADE ESTA LÍNEA AQUÍ ###
                # Registra el evento en el módulo C++ con la información relevante
                log_data = f"Archivo Procesado: {ruta_archivo}|Hash:{file_hash}|VT_Positivos:{vt_positives}/{vt_total}|Directorio:{directorio}|Extension:{extension}|Es_Sospechoso_Fijo:{'Si' if es_sospechoso else 'No'}"
                registrar_dato_en_c(log_data)
                ### FIN DE LA ADICIÓN ###

            # Reentrenar el modelo si se ha procesado un número suficiente de nuevos archivos
            if (self.perfil["total_files_processed"] - self.perfil["last_trained_count"]) >= self.reentrenamiento_intervalo:
                self._entrenar_modelo()

    def _entrenar_modelo(self):
        """
        Entrena o reentrena el modelo de Isolation Forest con los datos recopilados.
        """
        if len(self.perfil["data_for_training"]) < self.aprendizaje_min_archivos:
            print(f"IA: Pocos datos para entrenar el modelo ({len(self.perfil['data_for_training'])}/{self.aprendizaje_min_archivos}).")
            return

        print(f"IA: Entrenando modelo de Isolation Forest con {len(self.perfil['data_for_training'])} muestras...")
        try:
            X = np.array(self.perfil["data_for_training"])
            
            # Asegurarse de que X tiene el número correcto de características (columnas)
            # para el entrenamiento. Si la IA falla, revisa este número.
            # Nuestro _obtener_caracteristicas_archivo devuelve 8 características.
            expected_features = 8 
            if X.shape[1] != expected_features:
                print(f"ADVERTENCIA: Número de características ({X.shape[1]}) no coincide con el esperado ({expected_features}). Revisar _obtener_caracteristicas_archivo.")
                # Aquí puedes optar por limpiar los datos inválidos o abortar el entrenamiento
                # Por simplicidad, abortaremos si no coinciden las características.
                return

            self.model = IsolationForest(random_state=42, n_estimators=100, contamination='auto')
            self.model.fit(X)
            joblib.dump(self.model, self.model_path)
            self.perfil["last_trained_count"] = self.perfil["total_files_processed"]
            print("IA: Modelo de Isolation Forest entrenado y guardado correctamente.")
        except Exception as e:
            print(f"IA: Error durante el entrenamiento del modelo: {e}")
            self.model = None # Reiniciar el modelo si falla el entrenamiento

    def es_anomalo(self, ruta_archivo, es_sospechoso_fijo=False):
        """
        Determina si un archivo es anómalo utilizando el perfil de IA y VirusTotal.
        Ahora recibe es_sospechoso_fijo para usarlo en el perfilado.
        """
        # Aseguramos que solo un hilo acceda al perfil y al modelo a la vez para la inferencia
        with self.lock:
            # Primero, obtener las características del archivo
            # Se registra la actividad con la bandera es_sospechoso_fijo
            # Esta llamada a registrar_actividad_archivo YA obtiene las características
            # y las almacena en self.perfil["data_for_training"].
            # La IA luego usa esas características para el entrenamiento.
            # Para la predicción, necesitamos las características del archivo actual.
            
            # Nota: la llamada a registrar_actividad_archivo aquí puede ser redundante
            # si el único propósito de es_anomalo es predecir y _perform_file_analysis_threaded
            # ya llama a registrar_actividad_archivo. Si ese es el caso, esta línea podría
            # eliminarse, pero por ahora, la mantendremos para asegurar el registro.
            # self.registrar_actividad_archivo(ruta_archivo, es_sospechoso=es_sospechoso_fijo) # COMENTADO: Registrar actividad ya ocurre en vasio.py

            # Para la predicción, necesitamos las características del archivo
            # Las obtenemos directamente aquí, sin guardarlas en data_for_training si no es necesario para la predicción
            file_hash = None
            try:
                file_hash = self.calculate_file_hash(ruta_archivo)
            except Exception as e:
                print(f"IA: Error al calcular hash para predicción de {ruta_archivo}: {e}")
                return False, "Error al calcular hash para predicción."

            vt_positives = 0
            vt_total = 0
            if file_hash and self.virustotal_api_key:
                vt_report = self._escanear_virustotal(file_hash)
                if vt_report:
                    vt_positives = vt_report.get('positives', 0)
                    vt_total = vt_report.get('total', 0)
            
            # Obtener las características del archivo actual para la predicción
            caracteristicas_prediccion = self._obtener_caracteristicas_archivo(
                ruta_archivo, 
                virustotal_positives=vt_positives, 
                virustotal_total=vt_total, 
                es_sospechoso_fijo=es_sospechoso_fijo
            )

            if caracteristicas_prediccion is None:
                return False, "No se pudieron obtener características para la IA."

            # Asegurarse de que el modelo esté entrenado y tenga suficientes datos
            if self.model is None or len(self.perfil["data_for_training"]) < self.aprendizaje_min_archivos:
                return False, "El modelo de IA aún no está entrenado o no hay suficientes datos."
            
            # La predicción con Isolation Forest devuelve -1 para anomalías y 1 para normal
            # Reshape el array de características a 2D (1 muestra, N características)
            caracteristicas_2d = caracteristicas_prediccion.reshape(1, -1)
            
            try:
                prediccion = self.model.predict(caracteristicas_2d)[0]
                if prediccion == -1:
                    return True, "Detectado como anómalo por el modelo de IA."
                else:
                    return False, "Considerado normal por el modelo de IA."
            except Exception as e:
                print(f"IA: Error durante la predicción del modelo para {ruta_archivo}: {e}")
                return False, f"Error en la predicción del modelo: {e}"

    def iniciar_monitoreo_directorios(self, directorios_a_monitorear, intervalo_segundos=3600):
        """
        Inicia un monitoreo periódico de los directorios especificados en un hilo separado.
        Escanea archivos y actualiza el perfil de actividad de la IA.
        """
        if not directorios_a_monitorear:
            print("Advertencia: No se especificaron directorios para el monitoreo de IA.")
            return

        print(f"IA: Iniciando monitoreo periódico de directorios: {directorios_a_monitorear} cada {intervalo_segundos} segundos.")
        while True:
            for directorio in directorios_a_monitorear:
                if os.path.exists(directorio) and os.path.isdir(directorio):
                    try:
                        # Usamos os.walk para recorrer el directorio y sus subdirectorios
                        for root, _, files in os.walk(directorio):
                            for file in files:
                                full_path = os.path.join(root, file)
                                # Registrar la actividad para el perfil y recopilar datos para el ML
                                self.registrar_actividad_archivo(full_path) # Aquí se llama sin es_sospechoso, usando el False por defecto
                    except Exception as e:
                        print(f"IA: Error al escanear directorio {directorio}: {e}")
                else:
                    print(f"IA: Directorio no encontrado o no es un directorio: {directorio}")
            
            # Guardar el perfil después de escanear todos los directorios en esta iteración
            self._guardar_perfil()
            
            time.sleep(intervalo_segundos)