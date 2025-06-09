# --- START OF FILE main.py ---

import tkinter as tk
import threading
import time
import queue
import os
from tkinter import messagebox

# Importa tus clases principales
from core import VasionCore
from GUI2 import VasionEliteGUI, show_splash_screen

def main():
    core = None
    main_root = None
    try:
        # --- 1. Crear la cola de eventos ---
        event_queue = queue.Queue()

        # --- 2. Preparar la GUI y mostrar el Splash Screen ---
        main_root = tk.Tk()
        main_root.withdraw()
        splash = show_splash_screen(main_root)
        main_root.update_idletasks()

        # --- 3. Inicializar el Core (backend) ---
        core = VasionCore(event_queue=event_queue)

        # Simular un poco más de carga
        time.sleep(1)

        # --- 4. Destruir el splash e iniciar la GUI principal ---
        splash.destroy()
        main_root.deiconify()

        gui = VasionEliteGUI(main_root, core)
        
        gui.listen_for_events(event_queue)

        # --- 5. Iniciar los hilos de monitoreo del Core ---
        core.start_monitoring_loop()

        # --- 6. Iniciar el bucle principal de la GUI ---
        main_root.mainloop()

    except Exception as e:
        print(f"Ha ocurrido un error fatal en el programa principal: {e}")
        # Muestra el error en una ventana emergente si es posible
        messagebox.showerror("Error Fatal", f"Ha ocurrido un error crítico y la aplicación debe cerrarse:\n\n{e}")
    finally:
        if core:
            core.stop()
        print("\nEcosistema Vasion detenido.")

if __name__ == "__main__":
    # Asegurarse de que el directorio de trabajo es el del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()

# --- END OF FILE main.py ---