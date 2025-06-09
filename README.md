# Vasion Security Suite - Elite Edition (Proyecto en Desarrollo)

¡Hola! Soy un desarrollador nuevo en el mundo de la programación (llevo aproximadamente una semana) y este es mi primer proyecto personal. He estado aprendiendo a unir diferentes piezas de código, a hacer pequeñas modificaciones y a corregir sintaxis todo con ayuda de IA para dar vida a esta suite de seguridad.

**Vasion Security Suite** es un proyecto objetivo de explorar la detección avanzada de anomalías en sistemas, utilizando la inteligencia artificial y la integración de diferentes lenguajes para un monitoreo de bajo nivel.

## Visión del Proyecto

Mi objetivo es construir un sistema de seguridad que no solo detecte amenazas, sino que también aprenda y se adapte continuamente al entorno de la máquina.

## Esquema Arquitectónico Actual (Planificado y en Proceso)

Mi visión incluye un flujo de trabajo que incorpora aprendizaje automático y retroalimentación continua:

Este es un esquema mental aproximadamente en conjunto con la ayuda de la IA 

+---------------------------------------------+
|                 VasionCore                  |
|                                             |
|   +---------------------------------------+ |
|   |       Bucle de Refinamiento (Python)    | |
|   |                                         | |
----->|   |  +-----------------+  (datos +           | |
(Datos   |   |  | Red Neuronal    |  salida de IF) --> | |
brutos  |   |  | (Clasificador)  |                    | |
de Rust/ |   |  +-------+---------+                    | |
C++/SQL) |   |          ^       |                      | |
|   |          |(resultado NN)                 | |
----->|   |          |       v                      | |
(Alerta   |   |  +-------+---------+                    | |
de alta   |   |  | IsolationForest |                    | |
confianza) |   |  | (Detector Anom.)| &lt;-- (datos +        | |
|   |  +-----------------+   resultado NN)    | |
|   |                                         | |
+---------------------------------------------+ |
|                                             |
+---------------------------------------------+

Además, tengo planes para una capa de análisis más profunda y un mecanismo de aprendizaje continuo:

+-------------------------+
|     Módulo 3 (Análisis  |
|     Profundo - NN)      |
|                         |
|   Resultado: SOSPECHOSO |
+------------+------------+
|
(Este evento y sus        +----------+
características se        |
usan como nuevo dato      | (Retroalimentación de aprendizaje)
de entrenamiento)         |
v+-----------------+      +-------------------------+
|     Módulo 1    | &lt;--- |  Mecanismo de Reentreno | ----> (Se actualiza
| (Triaje Rápido) |      |     Online / Continuo   |       el modelo
+-----------------+      +-------------------------+       en vivo)

Todos los módulos de IA separados deben compartir información para aprender y no ser condicionados por un virus que lance programas benignos para condicionar, etc.

## Características Actuales

A día de hoy, el proyecto cuenta con:
* Interfaz Gráfica de Usuario (GUI) con Tkinter, aunque se debe de configurar porque aun lo estoy desarrollando
* Monitoreo básico de procesos (listas blancas/negras).
* Escaneo de archivos con detección de anomalías usando `IsolationForest`.
* Integración básica con C++ para el registro de metadatos (`metadata.db`).
* Conector inicial con Rust (`vasion_bridge`).
* Funcionalidades de notificación por correo electrónico y cifrado de configuración.

## Tecnologías Utilizadas

* **Python:** Para la lógica principal, GUI y Machine Learning.
* **C++:** Para funciones de registro de bajo nivel.
* **Rust:** Para monitoreo del sistema y posibles operaciones de bajo nivel (en desarrollo).
* **SQLite:** Para bases de datos locales.
* **Scikit-learn:** Para modelos de ML.
* **Tkinter:** Para la interfaz gráfica.

## Cómo Ejecutar el Proyecto (Configuración Inicial)

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/TuUsuario/Vasion-Security-Suite.git](https://github.com/TuUsuario/Vasion-Security-Suite.git)
    cd Vasion-Security-Suite
    ```
2.  **Configurar el entorno Python:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate # En Windows
    source venv/bin/activate # En Linux/macOS
    ```
3.  **Instalar dependencias de Python:**
    ```bash
    pip install psutil Pillow scikit-learn cryptography requests tk # Agrega tensorflow si ya lo usas, o planeas usarlo pronto
    ```
4.  **Compilar el módulo C++:**
    * Necesitarás un compilador C++ (MinGW en Windows, GCC/Clang en Linux/macOS).
    * En Windows, compila `basededatos.cpp` a `db_module.dll`.
        ```bash
        g++ -shared -o db_module.dll basededatos.cpp
        ```
    * En Linux, compila a `libdb_module.so`.
        ```bash
        g++ -shared -fPIC -o libdb_module.so basededatos.cpp
        ```
5.  **Compilar el módulo Rust:**
    * Necesitarás [Rustup](https://rustup.rs/) para instalar Rust.
    * Navega a la carpeta donde está `lib.rs` (ej. `connectors/vasion_bridge/` si la estructura lo permite) y ejecuta:
        ```bash
        cargo build --release
        ```
        Esto generará `vasion_bridge.dll` (Windows) o `libvasion_bridge.so` (Linux/macOS) en `target/release/`. Deberás copiar este archivo a la raíz de tu proyecto o a la carpeta donde Python espera encontrarlo.
6.  **Crear `config.json`:**
    * Crea un archivo llamado `config.json` en la raíz del proyecto con la siguiente estructura 
        ```json
      {
    "VIRUSTOTAL_API_KEY": "TU_API_KEY_AQUI",
    "admin_password": "TU_CONTRASEÑA_ADMIN_AQUI",
    "ADMIN_PASSWORD": "TU_CONTRASEÑA_ADMIN_AQUI",
    "correo_programador": "tu_correo@ejemplo.com",
    "contrasena_programador": "TU_CONTRASEÑA_CORREO_AQUI",
    "password_cierre": "TU_CONTRASEÑA_CIERRE_AQUI"
     }
        ```
7.  **Ejecutar la aplicación:**
    ```bash
    python main.py
    ```

## Cómo Contribuir

¡Estoy empezando en esto y agradecería enormemente cualquier tipo de ayuda, feedback o colaboración! Si tienes ideas, encuentras un error, o quieres ayudar a implementar alguna de las características planificadas
* Contactarme directamente si quieres discutir más a fondo.
Estoy abierto a aprender y a que este proyecto crezca con la ayuda de la comunidad.
ademas de afirmar que no se nada de programar solo me apoye con la IA modifique algunos bloques
mejore otros, arregle la sintaxis y le fui preguntando sobre algunas formar de optimizar o incluir mejoras, Este proyecto es de código abierto bajo la Licencia MIT. Siéntase libre de utilizarlo, modificarlo y distribuirlo, no debe de ser un 
reemplazo para los antivirus ni un EDM me gustaria una fomra de integrarlos, cooperar con informacion datos etc.
Gracias
