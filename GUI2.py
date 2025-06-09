# --- START OF FILE GUI2.py ---

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext, filedialog, Menu
import time
import os
import sys
import threading
import queue
from PIL import Image, ImageTk, ImageSequence

class VasionEliteGUI:
    def __init__(self, root, vasion_core):
        self.root = root
        self.vasion_core = vasion_core
        self.root.title("Vasion Security Suite - Elite Edition")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 750)
        self.root.resizable(True, True)

        self.themes = {
            "dark": {"bg_main": "#1A2530", "bg_panel": "#283C4B", "bg_header": "#1A2530", "text_primary": "#E0E6EB", "text_secondary": "#A0B0BB", "accent_blue": "#00BFFF", "accent_green": "#00D68F", "accent_orange": "#FF8C00", "accent_red": "#FF4500", "border_light": "#3C5060", "separator": "#4A6278", "tooltip_bg": "#ffffe0", "tooltip_fg": "#333333"},
            "light": {"bg_main": "#F0F0F0", "bg_panel": "#FFFFFF", "bg_header": "#E0E0E0", "text_primary": "#333333", "text_secondary": "#666666", "accent_blue": "#1E90FF", "accent_green": "#32CD32", "accent_orange": "#FFA500", "accent_red": "#DC143C", "border_light": "#CCCCCC", "separator": "#BBBBBB", "tooltip_bg": "#FFFFCC", "tooltip_fg": "#333333"}
        }
        self.current_theme_name = "dark"
        self.current_theme = self.themes[self.current_theme_name]

        self.monitoreo_activo = False
        self.log_buffer = []
        self.is_scanning = False
        self.loading_animation_id = None
        self.loading_frames = []
        self.loading_frame_index = 0
        self.notification_frame = None
        self.notification_label = None
        self.notification_timer_id = None

        self.icon_dashboard = self.icon_monitoreo = self.icon_herramientas = self.icon_configuracion = self.icon_acerca_de = self.icon_sun = self.icon_moon = self.current_theme_icon = None

        self._crear_interfaz()
        self._iniciar_actualizaciones_periodicas()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _apply_theme(self):
        self.root.configure(bg=self.current_theme["bg_main"])
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=self.current_theme["bg_main"], foreground=self.current_theme["text_primary"], font=('Segoe UI', 10))
        style.configure('TFrame', background=self.current_theme["bg_main"])
        style.configure('Panel.TFrame', background=self.current_theme["bg_panel"], relief='flat', borderwidth=0)
        style.configure('Card.TFrame', background=self.current_theme["bg_panel"], relief='solid', borderwidth=1, bordercolor=self.current_theme["border_light"])
        style.configure('TLabelframe', background=self.current_theme["bg_panel"], foreground=self.current_theme["text_primary"], bordercolor=self.current_theme["border_light"], relief='solid', borderwidth=1)
        style.configure('TLabelframe.Label', background=self.current_theme["bg_panel"], foreground=self.current_theme["text_primary"], font=('Segoe UI', 13, 'bold'))
        style.configure('TNotebook', background=self.current_theme["bg_main"], bordercolor=self.current_theme["border_light"], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', self.current_theme["bg_panel"]), ('!selected', self.current_theme["bg_main"])], foreground=[('selected', self.current_theme["accent_blue"]), ('!selected', self.current_theme["text_primary"])], font=[('selected', ('Segoe UI', 12, 'bold')), ('!selected', ('Segoe UI', 11))], expand=[('selected', [1,1,1,1])])
        style.configure('TNotebook.Tab', padding=[25, 12], anchor="w")
        style.configure('TButton', background=self.current_theme["bg_panel"], foreground=self.current_theme["text_primary"], font=('Segoe UI', 11, 'bold'), padding=12, relief='flat', borderwidth=0, focuscolor=self.current_theme["accent_blue"])
        style.map('TButton', background=[('active', self.current_theme["accent_blue"]), ('pressed', self.current_theme["accent_blue"])], foreground=[('active', self.current_theme["text_primary"])])
        style.configure('Action.TButton', background=self.current_theme["accent_blue"], foreground=self.current_theme["bg_main"], font=('Segoe UI', 11, 'bold'), padding=12, relief='flat', borderwidth=0)
        style.map('Action.TButton', background=[('active', self.current_theme["accent_green"]), ('pressed', self.current_theme["accent_blue"])], foreground=[('active', self.current_theme["bg_main"])])
        style.configure('Danger.TButton', background=self.current_theme["accent_red"], foreground=self.current_theme["text_primary"], font=('Segoe UI', 11, 'bold'), padding=12, relief='flat')
        style.map('Danger.TButton', background=[('active', '#CC3300')])
        style.configure('TEntry', fieldbackground=self.current_theme["bg_main"], foreground=self.current_theme["text_primary"], bordercolor=self.current_theme["border_light"], insertbackground=self.current_theme["accent_blue"], relief='solid', borderwidth=1, padding=5)
        style.configure('TSeparator', background=self.current_theme["separator"])
        style.configure("Custom.Horizontal.TProgressbar", background=self.current_theme["accent_green"], troughcolor=self.current_theme["bg_main"], bordercolor=self.current_theme["border_light"], borderwidth=1, thickness=10)
        style.configure('Treeview', background=self.current_theme["bg_main"], foreground=self.current_theme["text_primary"], fieldbackground=self.current_theme["bg_main"], bordercolor=self.current_theme["border_light"], rowheight=28, relief='flat')
        style.configure('Treeview.Heading', background=self.current_theme["bg_panel"], foreground=self.current_theme["accent_blue"], font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', self.current_theme["accent_blue"])], foreground=[('selected', self.current_theme["bg_main"])])
        for widget in self.root.winfo_children(): self._update_widget_colors(widget)
        if hasattr(self, 'btn_toggle_theme') and self.btn_toggle_theme.winfo_exists():
            self.current_theme_icon = self.icon_sun if self.current_theme_name == "dark" else self.icon_moon
            self.btn_toggle_theme.config(image=self.current_theme_icon)

    def _update_widget_colors(self, widget):
        try:
            widget_class = widget.winfo_class()
            bg_color = None
            if widget_class in ['TFrame', 'Frame', 'TLabel', 'Label', 'Canvas']:
                bg_color = self.current_theme["bg_panel"]
            if widget_class == 'ScrolledText':
                widget.config(background=self.current_theme["bg_main"], foreground=self.current_theme["text_secondary"], insertbackground=self.current_theme["accent_blue"])
            if 'background' in widget.configure() and bg_color:
                 widget.config(background=bg_color)
            if 'foreground' in widget.configure() and widget_class in ['TLabel', 'Label']:
                 if widget.cget('foreground') not in [self.themes['dark']['accent_green'], self.themes['dark']['accent_red'], self.themes['dark']['accent_blue'], self.themes['dark']['accent_orange']]:
                    widget.config(foreground=self.current_theme["text_primary"])
        except tk.TclError: pass
        for child in widget.winfo_children(): self._update_widget_colors(child)

    def _toggle_theme(self):
        self.current_theme_name = "light" if self.current_theme_name == "dark" else "dark"
        self.current_theme = self.themes[self.current_theme_name]
        self._apply_theme()
        self.show_notification(f"Tema cambiado a: {self.current_theme_name.capitalize()}", duration=2000)
    
    def listen_for_events(self, event_queue):
        try:
            while True:
                event_data = event_queue.get_nowait()
                self.process_core_event(event_data)
        except queue.Empty:
            pass
        self.root.after(100, self.listen_for_events, event_queue)

    def process_core_event(self, event_data):
        message = f"[{event_data.get('component', 'CORE')}] {event_data.get('message', 'Mensaje desconocido')}"
        event_type = event_data.get("event_type", "INFO").lower()
        notification_map = {"info": "info", "success": "success", "warning": "warning", "error": "error", "critical": "error"}
        gui_notification_type = notification_map.get(event_type, "info")
        is_alert = event_type in ["warning", "error", "critical"]
        self.agregar_evento_historial(message, is_alert=is_alert, event_type=gui_notification_type)
        if is_alert:
            self.show_notification(event_data.get('message'), notification_type=gui_notification_type)

    def _crear_interfaz(self):
        self._load_icons()
        main_container = ttk.Frame(self.root, style='TFrame')
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        sidebar_frame = ttk.Frame(main_container, style='Panel.TFrame')
        sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sidebar_frame.columnconfigure(0, weight=1)
        header_frame = ttk.Frame(sidebar_frame, style='Panel.TFrame')
        header_frame.pack(pady=(20, 10))
        ttk.Label(header_frame, text="Vasion", font=('Segoe UI', 16, 'bold'), foreground=self.current_theme["accent_green"], background=self.current_theme["bg_panel"]).pack(side=tk.LEFT)
        self.current_theme_icon = self.icon_sun if self.current_theme_name == "dark" else self.icon_moon
        self.btn_toggle_theme = ttk.Button(header_frame, image=self.current_theme_icon, style='TButton', command=self._toggle_theme)
        self.btn_toggle_theme.pack(side=tk.RIGHT, padx=(10,0))
        self._create_tooltip(self.btn_toggle_theme, "Alternar tema oscuro/claro")
        ttk.Separator(sidebar_frame, orient='horizontal', style='TSeparator').pack(fill=tk.X, padx=10, pady=5)
        self.notebook_tabs_frame = ttk.Frame(sidebar_frame, style='Panel.TFrame')
        self.notebook_tabs_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        buttons_data = [
            ("Dashboard", self.icon_dashboard, "tab_dashboard", "Vista general del sistema."),
            ("Monitoreo", self.icon_monitoreo, "tab_monitoreo", "Monitoreo detallado de eventos y procesos."),
            ("Herramientas", self.icon_herramientas, "tab_herramientas", "Utilidades y herramientas de análisis."),
            ("Configuración", self.icon_configuracion, "tab_configuracion", "Ajustes del sistema Vasion."),
            ("Acerca de", self.icon_acerca_de, "tab_acerca_de", "Información sobre la aplicación.")
        ]
        for text, icon, tab_name, tooltip_text in buttons_data:
            btn = ttk.Button(self.notebook_tabs_frame, text=f"  {text}", image=icon, compound=tk.LEFT, style='TButton', command=lambda t=tab_name: self.notebook.select(getattr(self, t)))
            btn.pack(fill=tk.X, padx=10, pady=5)
            self._create_tooltip(btn, tooltip_text)
        self.btn_more_actions = ttk.Button(self.notebook_tabs_frame, text="  Más Acciones", style='Action.TButton')
        self.btn_more_actions.pack(fill=tk.X, padx=10, pady=(20,5))
        self.more_actions_menu = tk.Menu(self.root, tearoff=0, bg=self.current_theme["bg_panel"], fg=self.current_theme["text_primary"])
        self.more_actions_menu.add_command(label="Reiniciar Servicios", command=self._reiniciar_servicios)
        self.more_actions_menu.add_command(label="Actualizar Base de Datos", command=self._actualizar_db)
        self.more_actions_menu.add_separator()
        self.more_actions_menu.add_command(label="Ayuda Online", command=self._mostrar_ayuda)
        self.btn_more_actions.bind("<Button-1>", self._show_more_actions_menu)
        ttk.Label(sidebar_frame, text="Usuario: Admin", font=('Segoe UI', 10), foreground=self.current_theme["text_secondary"], background=self.current_theme["bg_panel"]).pack(side=tk.BOTTOM, pady=10)
        self.notebook = ttk.Notebook(main_container, style='TNotebook')
        self.notebook.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.tab_dashboard = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.tab_monitoreo = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.tab_herramientas = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.tab_configuracion = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.tab_acerca_de = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_monitoreo, text="Monitoreo")
        self.notebook.add(self.tab_herramientas, text="Herramientas")
        self.notebook.add(self.tab_configuracion, text="Configuración")
        self.notebook.add(self.tab_acerca_de, text="Acerca de")
        self._crear_tab_dashboard(self.tab_dashboard)
        self._crear_tab_monitoreo(self.tab_monitoreo)
        self._crear_tab_herramientas(self.tab_herramientas)
        self._crear_tab_configuracion(self.tab_configuracion)
        self._crear_tab_acerca_de(self.tab_acerca_de)
        self.status_bar = ttk.Label(self.root, text="Vasion System: Iniciado...", relief=tk.FLAT, anchor=tk.W, background=self.current_theme["bg_header"], foreground=self.current_theme["text_secondary"], font=('Segoe UI', 9, 'italic'), padding=[15, 8])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self._create_notification_area()
        self._apply_theme()

    def _load_icons(self):
        try:
            icon_size = (24, 24)
            self.icon_dashboard = ImageTk.PhotoImage(Image.open("dashboard_icon.png").resize(icon_size, Image.LANCZOS))
            self.icon_monitoreo = ImageTk.PhotoImage(Image.open("monitoreo_icon.png").resize(icon_size, Image.LANCZOS))
            self.icon_herramientas = ImageTk.PhotoImage(Image.open("herramientas_icon.png").resize(icon_size, Image.LANCZOS))
            self.icon_configuracion = ImageTk.PhotoImage(Image.open("configuracion_icon.png").resize(icon_size, Image.LANCZOS))
            self.icon_acerca_de = ImageTk.PhotoImage(Image.open("acerca_de_icon.png").resize(icon_size, Image.LANCZOS))
            self.icon_sun = ImageTk.PhotoImage(Image.open("sun_icon.png").resize((18, 18), Image.LANCZOS))
            self.icon_moon = ImageTk.PhotoImage(Image.open("moon_icon.png").resize((18, 18), Image.LANCZOS))
            img_path = "loading_spinner.gif"
            if os.path.exists(img_path):
                gif_image = Image.open(img_path)
                for frame in ImageSequence.Iterator(gif_image):
                    self.loading_frames.append(ImageTk.PhotoImage(frame.resize((30, 30), Image.LANCZOS)))
        except Exception as e:
            messagebox.showerror("Error de Íconos", f"No se pudieron cargar los recursos visuales: {e}")

    def _create_tooltip(self, widget, text):
        pass # Implementación simple

    def _create_notification_area(self):
        self.notification_frame = tk.Frame(self.root, bd=0, relief=tk.FLAT)
        self.notification_frame.place(relx=1.0, rely=0, x=-20, y=20, anchor=tk.NE)
        self.notification_label = tk.Label(self.notification_frame, text="", font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        self.notification_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.notification_close_button = tk.Button(self.notification_frame, text="✖", font=('Segoe UI', 8, 'bold'), command=self._hide_notification, relief=tk.FLAT, bd=0)
        self.notification_close_button.pack(side=tk.RIGHT, padx=(0, 5))
        self.notification_frame.place_forget()

    def show_notification(self, message, notification_type="info", duration=5000):
        if self.notification_timer_id: self.root.after_cancel(self.notification_timer_id)
        colors = {"info": {"bg": self.current_theme["accent_blue"], "fg": self.current_theme["bg_main"]}, "success": {"bg": self.current_theme["accent_green"], "fg": self.current_theme["bg_main"]}, "warning": {"bg": self.current_theme["accent_orange"], "fg": self.current_theme["bg_main"]}, "error": {"bg": self.current_theme["accent_red"], "fg": self.current_theme["text_primary"]}}
        chosen_colors = colors.get(notification_type, colors["info"])
        self.notification_frame.config(bg=chosen_colors["bg"])
        self.notification_label.config(text=message, bg=chosen_colors["bg"], fg=chosen_colors["fg"])
        self.notification_close_button.config(bg=chosen_colors["bg"], fg=chosen_colors["fg"])
        self.notification_frame.place(relx=1.0, rely=0, x=-20, y=20, anchor=tk.NE)
        self.notification_timer_id = self.root.after(duration, self._hide_notification)

    def _hide_notification(self):
        if self.notification_timer_id:
            self.root.after_cancel(self.notification_timer_id)
            self.notification_timer_id = None
        self.notification_frame.place_forget()

    def _start_loading_animation(self, parent_widget, message="Cargando..."):
        self.loading_frame = tk.Frame(parent_widget, bg=self.current_theme["bg_panel"])
        self.loading_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=300, height=100)
        self.loading_frame.lift()
        if self.loading_frames:
            self.loading_label = tk.Label(self.loading_frame, bg=self.current_theme["bg_panel"])
            self.loading_label.pack(pady=5)
            self._animate_loading_gif()
        else:
            self.loading_label = ttk.Label(self.loading_frame, text=".", font=('Segoe UI', 20, 'bold'), background=self.current_theme["bg_panel"], foreground=self.current_theme["accent_blue"])
            self.loading_label.pack(pady=5)
            self._animate_loading_dots()
        ttk.Label(self.loading_frame, text=message, font=('Segoe UI', 11), background=self.current_theme["bg_panel"], foreground=self.current_theme["text_secondary"]).pack(pady=5)
        self.is_scanning = True
        self.root.update_idletasks()

    def _animate_loading_dots(self, dots="."):
        if not self.is_scanning: return
        self.loading_label.config(text=dots)
        new_dots = dots + "." if len(dots) < 3 else "."
        self.loading_animation_id = self.root.after(500, self._animate_loading_dots, new_dots)

    def _animate_loading_gif(self):
        if not self.is_scanning or not self.loading_frames: return
        self.loading_frame_index = (self.loading_frame_index + 1) % len(self.loading_frames)
        frame = self.loading_frames[self.loading_frame_index]
        self.loading_label.config(image=frame)
        self.loading_animation_id = self.root.after(100, self._animate_loading_gif)

    def _stop_loading_animation(self):
        self.is_scanning = False
        if self.loading_animation_id:
            self.root.after_cancel(self.loading_animation_id)
            self.loading_animation_id = None
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()

    def _crear_tab_dashboard(self, parent_frame):
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.rowconfigure(1, weight=1)
        card_status = ttk.Frame(parent_frame, style='Card.TFrame', padding=20)
        card_status.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        card_actions = ttk.Frame(parent_frame, style='Card.TFrame', padding=20)
        card_actions.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        card_events = ttk.Frame(parent_frame, style='Card.TFrame', padding=20)
        card_events.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        ttk.Label(card_actions, text="ACCIONES RÁPIDAS", font=("Segoe UI", 12, 'bold'), foreground=self.current_theme["accent_blue"], background=self.current_theme["bg_panel"]).pack(pady=(0,10), anchor=tk.W)
        ttk.Button(card_actions, text="⚡ Escaneo Profundo de Archivos", command=self._escanear_archivos_rapido, style='Action.TButton').pack(fill=tk.X, pady=6)
        ttk.Label(card_events, text="EVENTOS RECIENTES", font=("Segoe UI", 12, 'bold'), foreground=self.current_theme["accent_blue"], background=self.current_theme["bg_panel"]).pack(pady=(0,10), anchor=tk.W)
        self.dashboard_event_log_text = scrolledtext.ScrolledText(card_events, wrap=tk.WORD, height=8, state=tk.DISABLED, background=self.current_theme["bg_main"], foreground=self.current_theme["text_secondary"], insertbackground=self.current_theme["accent_blue"], borderwidth=0, relief='flat', font=('Consolas', 9))
        self.dashboard_event_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _crear_tab_monitoreo(self, parent_frame):
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(1, weight=1)
        top_panel = ttk.LabelFrame(parent_frame, text="Procesos del Sistema", padding=15, style='TLabelframe')
        top_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        top_panel.columnconfigure(0, weight=1)
        top_panel.rowconfigure(1, weight=1)
        controls_frame = ttk.Frame(top_panel, style='Panel.TFrame')
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        ttk.Label(controls_frame, text="Filtrar:", background=self.current_theme["bg_panel"]).grid(row=0, column=0, padx=(0,5))
        self.filter_entry = ttk.Entry(controls_frame, style='TEntry')
        self.filter_entry.grid(row=0, column=1, sticky="ew")
        btn_actualizar = ttk.Button(controls_frame, text="🔄 Actualizar", command=self._actualizar_lista_procesos, style='Action.TButton')
        btn_actualizar.grid(row=0, column=2, padx=(10,0))
        columns = ("PID", "Nombre", "Usuario", "Estado", "CPU%", "Memoria")
        self.process_tree = ttk.Treeview(top_panel, columns=columns, show="headings", style='Treeview')
        for col in columns: self.process_tree.heading(col, text=col, anchor=tk.W)
        self.process_tree.column("PID", width=80, stretch=tk.NO)
        self.process_tree.column("Nombre", width=250)
        self.process_tree.column("Usuario", width=150)
        self.process_tree.column("Estado", width=100)
        self.process_tree.column("CPU%", width=80, stretch=tk.NO)
        self.process_tree.column("Memoria", width=120, stretch=tk.NO)
        vsb = ttk.Scrollbar(top_panel, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=vsb.set)
        self.process_tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        log_panel = ttk.LabelFrame(parent_frame, text="Registro Completo de Eventos", padding=15, style='TLabelframe')
        log_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        log_panel.columnconfigure(0, weight=1)
        log_panel.rowconfigure(0, weight=1)
        self.texto_historial = scrolledtext.ScrolledText(log_panel, wrap=tk.WORD, height=10, state=tk.DISABLED, background=self.current_theme["bg_main"], foreground=self.current_theme["text_secondary"], insertbackground=self.current_theme["accent_blue"], borderwidth=0, relief='flat', font=('Consolas', 9))
        self.texto_historial.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _crear_tab_herramientas(self, parent_frame):
        ttk.Label(parent_frame, text="Herramientas (Aún no implementadas)").pack(pady=20)

    def _crear_tab_configuracion(self, parent_frame):
        ttk.Label(parent_frame, text="Configuración (Aún no implementada)").pack(pady=20)

    def _crear_tab_acerca_de(self, parent_frame):
        ttk.Label(parent_frame, text="Vasion Security Suite\nVersión Alpha").pack(pady=20)

    def _iniciar_actualizaciones_periodicas(self):
        pass

    def _escanear_archivos_rapido(self):
        if self.is_scanning:
            self.show_notification("Ya se está realizando un escaneo.", "info")
            return
        directorio_a_escanear = filedialog.askdirectory(title="Selecciona una carpeta para el escaneo profundo")
        if not directorio_a_escanear:
            self.show_notification("Escaneo cancelado.", "info")
            return
        self.status_bar.config(text=f"Estado: Escaneando {directorio_a_escanear}...")
        self._start_loading_animation(self.tab_dashboard, message=f"Analizando {os.path.basename(directorio_a_escanear)}...")
        threading.Thread(target=self.vasion_core.escanear_directorio_completo, args=(directorio_a_escanear, self._escaneo_completado_callback), daemon=True).start()

    def _escaneo_completado_callback(self, resultados):
        def update_gui():
            self._stop_loading_animation()
            anomalias = resultados.get("anomalias", 0)
            if anomalias > 0:
                self.status_bar.config(text=f"Estado: Escaneo completado. ¡Se encontraron {anomalias} anomalías!", foreground=self.current_theme["accent_red"])
                messagebox.showwarning("Escaneo Completo", f"Escaneo finalizado. ¡Se encontraron {anomalias} anomalías!\nRevisa el log para más detalles.")
            else:
                self.status_bar.config(text="Estado: Escaneo completado. Sistema seguro.", foreground=self.current_theme["accent_green"])
                messagebox.showinfo("Escaneo Completo", "Escaneo profundo de archivos finalizado. No se encontraron anomalías.")
        self.root.after(0, update_gui)

    def _actualizar_lista_procesos(self):
        if self.is_scanning:
            self.show_notification("Otra operación ya está en curso.", "warning")
            return
        self._start_loading_animation(self.tab_monitoreo, message="Cargando procesos...")
        threading.Thread(target=self._worker_actualizar_procesos, daemon=True).start()

    def _worker_actualizar_procesos(self):
        lista_procesos_reales = self.vasion_core.obtener_lista_procesos()
        self.root.after(0, self._populate_process_tree, lista_procesos_reales)

    def _populate_process_tree(self, lista_procesos):
        self._stop_loading_animation()
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        for proc_data in lista_procesos:
            self.process_tree.insert("", tk.END, values=proc_data)
        self.show_notification("Lista de procesos actualizada.", "success", 2000)

    def _gestionar_listas(self):
        """Abre una ventana para gestionar la whitelist y la blacklist."""
        
        # Crear la ventana emergente (Toplevel)
        win_listas = tk.Toplevel(self.root)
        win_listas.title("Gestión de Listas de Procesos")
        win_listas.geometry("600x450")
        win_listas.configure(bg=self.current_theme["bg_main"])
        win_listas.transient(self.root) # Mantiene la ventana por encima de la principal
        win_listas.grab_set() # Bloquea la interacción con la ventana principal

        # --- Frames para cada lista ---
        frame_blanca = ttk.LabelFrame(win_listas, text="✅ Whitelist (Procesos Permitidos)", padding=10)
        frame_blanca.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        frame_negra = ttk.LabelFrame(win_listas, text="🚫 Blacklist (Procesos a Vigilar)", padding=10)
        frame_negra.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Función para poblar las listas ---
    def refrescar_listas():
        listas_actuales = self.vasion_core.cargar_listas_procesos()
            
            # Limpiar vistas
        listbox_blanca.delete(0, tk.END)
        listbox_negra.delete(0, tk.END)
            
            # Llenar vistas
        for item in sorted(listas_actuales.get("whitelist", [])):
                listbox_blanca.insert(tk.END, item)
        for item in sorted(listas_actuales.get("blacklist", [])):
                listbox_negra.insert(tk.END, item)

        # --- Widgets de la Whitelist ---
        listbox_blanca = tk.Listbox(frame_blanca, bg=self.current_theme["bg_main"], fg=self.current_theme["text_primary"], selectbackground=self.current_theme["accent_blue"], borderwidth=0, highlightthickness=0)
        listbox_blanca.pack(fill=tk.BOTH, expand=True, pady=5)
        
        entry_blanca = ttk.Entry(frame_blanca, style='TEntry')
        entry_blanca.pack(fill=tk.X, pady=(5,0))
        
        # --- Widgets de la Blacklist ---
        listbox_negra = tk.Listbox(frame_negra, bg=self.current_theme["bg_main"], fg=self.current_theme["text_primary"], selectbackground=self.current_theme["accent_blue"], borderwidth=0, highlightthickness=0)
        listbox_negra.pack(fill=tk.BOTH, expand=True, pady=5)

        entry_negra = ttk.Entry(frame_negra, style='TEntry')
        entry_negra.pack(fill=tk.X, pady=(5,0))

        # --- Funciones de los botones ---
    def agregar(nombre_lista, entry_widget):
        proceso = entry_widget.get()
        if self.vasion_core.agregar_a_lista(nombre_lista, proceso):
            entry_widget.delete(0, tk.END)
            refrescar_listas()

    def eliminar(nombre_lista, listbox_widget):
        seleccion = listbox_widget.curselection()
        if seleccion:
            proceso = listbox_widget.get(seleccion[0])
            if self.vasion_core.eliminar_de_lista(nombre_lista, proceso):
                refrescar_listas()

        # --- Botones ---
        btn_frame_blanca = ttk.Frame(frame_blanca)
        btn_frame_blanca.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame_blanca, text="Añadir", command=lambda: agregar("whitelist", entry_blanca)).pack(side=tk.LEFT, expand=True)
        ttk.Button(btn_frame_blanca, text="Eliminar", command=lambda: eliminar("whitelist", listbox_blanca)).pack(side=tk.RIGHT, expand=True)

        btn_frame_negra = ttk.Frame(frame_negra)
        btn_frame_negra.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame_negra, text="Añadir", command=lambda: agregar("blacklist", entry_negra)).pack(side=tk.LEFT, expand=True)
        ttk.Button(btn_frame_negra, text="Eliminar", command=lambda: eliminar("blacklist", listbox_negra)).pack(side=tk.RIGHT, expand=True)

        # Carga inicial de datos
        refrescar_listas()    

    def _on_closing(self):
        if messagebox.askokcancel("Cerrar Vasion", "¿Estás seguro de que quieres cerrar Vasion?"):
            self.root.destroy()
    
    def _show_more_actions_menu(self, event):
        try:
            self.more_actions_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.more_actions_menu.grab_release()

    def _reiniciar_servicios(self):
        messagebox.showinfo("Función no implementada", "La lógica para reiniciar servicios aún no está conectada al Core.")

    def _actualizar_db(self):
        messagebox.showinfo("Función no implementada", "La lógica para actualizar la base de datos aún no está conectada.")

    def _mostrar_ayuda(self):
        messagebox.showinfo("Ayuda", "Se abriría la documentación online de Vasion.")

    def agregar_evento_historial(self, evento, is_alert=False, event_type="info"):
        timestamp_event = f"[{time.strftime('%H:%M:%S')}] {evento}"
        if hasattr(self, 'texto_historial') and self.texto_historial.winfo_exists():
            self.texto_historial.config(state=tk.NORMAL)
            self.texto_historial.insert(tk.END, f"{timestamp_event}\n")
            self.texto_historial.see(tk.END)
            self.texto_historial.config(state=tk.DISABLED)
        if is_alert and hasattr(self, 'dashboard_event_log_text') and self.dashboard_event_log_text.winfo_exists():
            self.dashboard_event_log_text.config(state=tk.NORMAL)
            self.dashboard_event_log_text.insert(tk.END, f"{timestamp_event}\n")
            self.dashboard_event_log_text.see(tk.END)
            self.dashboard_event_log_text.config(state=tk.DISABLED)

def show_splash_screen(root):
    splash_root = tk.Toplevel(root)
    splash_root.overrideredirect(True)
    w, h = 400, 300
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    splash_root.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
    splash_frame = tk.Frame(splash_root, bg="#1A2530")
    splash_frame.pack(expand=True, fill=tk.BOTH)
    try:
        logo_path = "vasion_logo.png"
        if os.path.exists(logo_path):
            logo_image = ImageTk.PhotoImage(Image.open(logo_path).resize((150, 150), Image.LANCZOS))
            logo_label = tk.Label(splash_frame, image=logo_image, bg="#1A2530")
            logo_label.image = logo_image
            logo_label.pack(pady=(20,10))
    except Exception as e:
        print(f"Error cargando logo del splash: {e}")
        ttk.Label(splash_frame, text="Vasion", font=("Segoe UI", 36, "bold"), foreground="#00D68F", background="#1A2530").pack(pady=(20,10))
    ttk.Label(splash_frame, text="Cargando componentes de seguridad...", font=("Segoe UI", 12), foreground="#A0B0BB", background="#1A2530").pack(pady=(5,20))
    splash_root.update_idletasks()
    return splash_root

# --- END OF FILE GUI2.py ---