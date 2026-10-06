import os
import sys
import json
import time
import datetime
import threading
import subprocess
import urllib.request
import tkinter as tk
import ssl
from tkinter import messagebox
import customtkinter as ctk
from fpdf import FPDF

# Fijar el directorio de trabajo en la raiz del ejecutable si esta congelado
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# --- CONTROL DE VERSIONES Y ACTUALIZACIONES ---
VERSION_ACTUAL = "1.2.5"
URL_VERSION_REMOTA = "https://raw.githubusercontent.com/ivaanjc/facturador-obrador/main/version.json"

# Configuracion visual moderna
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- CONTEXTO SSL PERMISIVO ---
def get_ssl_context():
    """Genera un contexto SSL sin validacion estricta para garantizar conexion en cualquier PC."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# --- RESOLUCION DE RUTAS ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    ASSET_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSET_DIR = BASE_DIR

# Carpeta de recursos adicionales (fuentes, logo e icono)
FUENTES_DIR = os.path.join(ASSET_DIR, 'fuentes-letra')
if not os.path.exists(FUENTES_DIR):
    FUENTES_DIR = os.path.join(BASE_DIR, 'fuentes-letra')

# Busqueda de logo.png dentro de fuentes-letra o en la raiz como respaldo
LOGO_FILE = os.path.join(FUENTES_DIR, 'logo.png')
if not os.path.exists(LOGO_FILE):
    LOGO_FILE = os.path.join(BASE_DIR, 'logo.png')

# Busqueda de icono.ico para ventanas
ICO_FILE = os.path.join(FUENTES_DIR, 'icono.ico')
if not os.path.exists(ICO_FILE):
    ICO_FILE = os.path.join(BASE_DIR, 'icono.ico')

CLIENTES_FILE = os.path.join(BASE_DIR, 'clientes.json')
PRODUCTOS_FILE = os.path.join(BASE_DIR, 'productos.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')


# --- PERSISTENCIA DE DATOS JSON ---
def cargar_json(ruta, datos_defecto):
    if not os.path.exists(ruta):
        guardar_json(ruta, datos_defecto)
        return datos_defecto
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()
            if not contenido:
                guardar_json(ruta, datos_defecto)
                return datos_defecto
            return json.loads(contenido)
    except Exception as e:
        messagebox.showwarning(
            "Aviso de lectura", 
            f"No se pudo leer '{os.path.basename(ruta)}': {e}.\nSe usaran datos temporales."
        )
        return datos_defecto

def guardar_json(ruta, datos):
    try:
        directorio = os.path.dirname(ruta)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)
            
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Error al guardar", f"No se pudo guardar en '{os.path.basename(ruta)}': {e}")
        return False


# --- LOGICA DE AUTO-ACTUALIZACION DIRECTA (.EXE) ---
def parse_version(v_str):
    try:
        limpio = v_str.strip().lstrip('v')
        return tuple(int(x) for x in limpio.split('.'))
    except Exception:
        return (0, 0, 0)

# --- MODAL MODERNO: NOTIFICACION DE ACTUALIZACION DISPONIBLE ---
class VentanaAvisoActualizacion(ctk.CTkToplevel):
    def __init__(self, master, version_remota, url_nuevo_exe):
        super().__init__(master)
        self.master = master
        self.version_remota = version_remota
        self.url_nuevo_exe = url_nuevo_exe

        self.title("Actualizacion disponible")
        self.geometry("460x320")
        self.resizable(False, False)
        self.grab_set()

        if os.path.exists(ICO_FILE):
            try:
                self.iconbitmap(ICO_FILE)
            except Exception:
                pass

        # Centrar respecto a la ventana principal
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - 230
        y = master.winfo_y() + (master.winfo_height() // 2) - 160
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Contenedor principal con margen
        container = ctk.CTkFrame(self, corner_radius=15, fg_color=("gray95", "gray14"))
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Encabezado visual
        lbl_icono = ctk.CTkLabel(container, text="🚀", font=("Helvetica", 34))
        lbl_icono.pack(pady=(12, 0))

        lbl_titulo = ctk.CTkLabel(
            container, 
            text="¡Nueva version disponible!", 
            font=("Helvetica", 16, "bold")
        )
        lbl_titulo.pack(pady=(2, 10))

        # Tarjeta informativa de versiones
        card = ctk.CTkFrame(container, corner_radius=10, fg_color=("gray88", "gray20"))
        card.pack(fill="x", padx=20, pady=5)

        fila_v_actual = ctk.CTkFrame(card, fg_color="transparent")
        fila_v_actual.pack(fill="x", padx=15, pady=(8, 2))
        ctk.CTkLabel(fila_v_actual, text="Version instalada:", font=("Helvetica", 12)).pack(side="left")
        ctk.CTkLabel(fila_v_actual, text=f"v{VERSION_ACTUAL}", font=("Helvetica", 12, "bold"), text_color="gray50").pack(side="right")

        fila_v_nueva = ctk.CTkFrame(card, fg_color="transparent")
        fila_v_nueva.pack(fill="x", padx=15, pady=(2, 8))
        ctk.CTkLabel(fila_v_nueva, text="Nueva version:", font=("Helvetica", 12)).pack(side="left")
        ctk.CTkLabel(fila_v_nueva, text=f"v{self.version_remota}", font=("Helvetica", 13, "bold"), text_color=("#1976d2", "#42a5f5")).pack(side="right")

        lbl_sub = ctk.CTkLabel(
            container, 
            text="La actualizacion se sobreescribira directamente en este archivo.",
            font=("Helvetica", 11),
            text_color=("gray40", "gray65")
        )
        lbl_sub.pack(pady=(8, 12))

        # Botones de accion
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        btn_cancelar = ctk.CTkButton(
            btn_frame, 
            text="Mas tarde", 
            width=110,
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray20", "gray85"),
            border_width=1,
            border_color=("gray70", "gray40"),
            command=self.destroy
        )
        btn_cancelar.pack(side="left", padx=(0, 10), fill="x", expand=True)

        btn_actualizar = ctk.CTkButton(
            btn_frame, 
            text="Actualizar ahora", 
            width=150,
            font=("Helvetica", 12, "bold"),
            fg_color="#2b7a78", 
            hover_color="#17252a",
            command=self._iniciar_descarga
        )
        btn_actualizar.pack(side="right", fill="x", expand=True)

    def _iniciar_descarga(self):
        url = self.url_nuevo_exe
        master = self.master
        self.destroy()
        VentanaDescarga(master, url)


# --- VENTANA DE PROGRESO Y REEMPLAZO DIRECTO EN DISCO ---
class VentanaDescarga(ctk.CTkToplevel):
    def __init__(self, master, url_nuevo_exe):
        super().__init__(master)
        self.master = master
        self.url_nuevo_exe = url_nuevo_exe
        
        self.title("Actualizando Facturador")
        self.geometry("450x220")
        self.resizable(False, False)
        self.grab_set()

        if os.path.exists(ICO_FILE):
            try:
                self.iconbitmap(ICO_FILE)
            except Exception:
                pass

        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - 225
        y = master.winfo_y() + (master.winfo_height() // 2) - 110
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        container = ctk.CTkFrame(self, corner_radius=15, fg_color=("gray95", "gray14"))
        container.pack(fill="both", expand=True, padx=15, pady=15)

        self.lbl_estado = ctk.CTkLabel(
            container, 
            text="Conectando con el servidor...", 
            font=("Helvetica", 14, "bold")
        )
        self.lbl_estado.pack(pady=(18, 12))

        self.progress_bar = ctk.CTkProgressBar(container, width=370, height=12, corner_radius=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=6)

        self.lbl_detalles = ctk.CTkLabel(
            container, 
            text="0.00 MB / 0.00 MB (0%)", 
            font=("Helvetica", 11),
            text_color=("gray40", "gray60")
        )
        self.lbl_detalles.pack(pady=(4, 10))

        self.lbl_aviso = ctk.CTkLabel(
            container,
            text="Descargando el ejecutable actualizado...",
            font=("Helvetica", 10),
            text_color="gray50"
        )
        self.lbl_aviso.pack(pady=(0, 10))

        self.protocol("WM_DELETE_WINDOW", lambda: None)
        threading.Thread(target=self._descargar_hilo, daemon=True).start()

    def _obtener_ruta_exe_real(self):
        """Devuelve la ruta absoluta del .exe real (por ejemplo en el Escritorio), evitando carpetas temporales."""
        ruta_encontrada = ""
        
        # 1. Intentar por Kernel32 GetModuleFileNameW (ruta nativa de proceso de Windows)
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetModuleFileNameW(0, buf, 1024)
            if buf.value and os.path.exists(buf.value):
                ruta_encontrada = os.path.normpath(buf.value)
        except Exception:
            pass

        # 2. Si apunta a una carpeta temporal _MEI de PyInstaller o esta vacia, usar sys.argv[0]
        if not ruta_encontrada or "_MEI" in ruta_encontrada:
            if getattr(sys, 'frozen', False):
                ruta_encontrada = os.path.normpath(os.path.abspath(sys.argv[0]))
            else:
                ruta_encontrada = os.path.normpath(os.path.abspath(__file__))

        # 3. Comprobar sys.executable como ultimo recurso si no es temporal
        if "_MEI" in ruta_encontrada:
            posible_exe = os.path.normpath(sys.executable)
            if "_MEI" not in posible_exe:
                ruta_encontrada = posible_exe

        return ruta_encontrada

    def _descargar_hilo(self):
        temp_dir = os.environ.get("TEMP", os.path.dirname(sys.executable))
        ruta_temporal_exe = os.path.join(temp_dir, "facturador_update.exe")

        try:
            req = urllib.request.Request(
                self.url_nuevo_exe,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )

            with urllib.request.urlopen(req, timeout=60, context=get_ssl_context()) as resp:
                total_bytes = resp.getheader('Content-Length')
                total_bytes = int(total_bytes) if total_bytes else None

                descargados = 0
                bloque_size = 1024 * 64
                
                with open(ruta_temporal_exe, 'wb') as f_out:
                    while True:
                        chunk = resp.read(bloque_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        descargados += len(chunk)

                        if total_bytes:
                            porcentaje = descargados / total_bytes
                            mb_actual = descargados / (1024 * 1024)
                            mb_total = total_bytes / (1024 * 1024)
                            texto_progreso = f"{mb_actual:.2f} MB / {mb_total:.2f} MB ({int(porcentaje * 100)}%)"
                            self.after(0, self._actualizar_ui, porcentaje, texto_progreso)

            tamano_mb = os.path.getsize(ruta_temporal_exe) / (1024 * 1024)
            if tamano_mb < 3.0:
                raise ValueError(f"Archivo incompleto o enlace incorrecto ({tamano_mb:.2f} MB).")

            self.after(0, self._finalizar_y_reemplazar, ruta_temporal_exe)

        except Exception as e:
            if os.path.exists(ruta_temporal_exe):
                try:
                    os.remove(ruta_temporal_exe)
                except Exception:
                    pass
            self.after(0, self._mostrar_error, str(e))

    def _finalizar_y_reemplazar(self, ruta_temporal_exe):
            self.lbl_estado.configure(text="Aplicando actualizacion...")
            self.lbl_aviso.configure(text="Sobreescribiendo ejecutable y finalizando...")

            ruta_exe_real = self._obtener_ruta_exe_real()
            directorio_actual = os.path.dirname(ruta_exe_real)
            pid_actual = os.getpid()

            temp_dir = os.environ.get("TEMP", directorio_actual)
            updater_bat = os.path.join(temp_dir, "reemplazar_update.bat")

            # Script por lotes que:
            # 1. Espera a que el proceso actual muera por PID para liberar el archivo .exe bloqueado
            # 2. Copia y sobreescribe con /Y el .exe directamente en su ruta original
            # 3. Elimina el archivo temporal de descarga
            # 4. Muestra un cuadro de confirmacion nativo (Si/No) preguntando si desea abrir el programa
            contenido_bat = (
                "@echo off\r\n"
                ":wait_proc\r\n"
                f'tasklist /fi "PID eq {pid_actual}" 2>NUL | find /I "{pid_actual}" >NUL\r\n'
                "if not errorlevel 1 (\r\n"
                "    timeout /t 1 /nobreak >nul\r\n"
                "    goto wait_proc\r\n"
                ")\r\n"
                "timeout /t 1 /nobreak >nul\r\n"
                f'copy /y "{ruta_temporal_exe}" "{ruta_exe_real}" >nul\r\n'
                f'del "{ruta_temporal_exe}" >nul 2>nul\r\n'
                'mshta vbscript:Execute("resp=MsgBox(""La actualizacion se ha completado correctamente." & vbCrLf & ""¿Desea abrir el programa ahora?"", 36, ""Actualizacion completada""): If resp=6 Then CreateObject(""WScript.Shell"").Run """""'
                f'{ruta_exe_real}'
                '""""": End If: close")\r\n'
                '(goto) 2>nul & del "%~f0"\r\n'
            )

            with open(updater_bat, "w", encoding="ascii", errors="ignore") as f:
                f.write(contenido_bat)

            # Lanzar el actualizador en segundo plano sin ventana de consola negra
            subprocess.Popen(
                ["cmd.exe", "/c", updater_bat],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                close_fds=True
            )

            self.master.destroy()
            sys.exit(0)

    def _actualizar_ui(self, porcentaje, texto):
        self.progress_bar.set(porcentaje)
        self.lbl_estado.configure(text="Descargando actualizacion...")
        self.lbl_detalles.configure(text=texto)

    def _mostrar_error(self, error_msg):
        self.destroy()
        messagebox.showerror(
            "Fallo al actualizar", 
            f"No se pudo completar la actualizacion:\n{error_msg}",
            parent=self.master
        )

def comprobar_actualizacion(parent=None, manual=False):
    if not getattr(sys, 'frozen', False):
        if manual:
            messagebox.showinfo(
                "Modo desarrollo", 
                "Estas ejecutando el script .py. Las actualizaciones automaticas funcionan sobre la app instalada (.exe).",
                parent=parent
            )
        return

    try:
        url_con_cache_bust = f"{URL_VERSION_REMOTA}?nocache={int(time.time())}"
        
        req = urllib.request.Request(
            url_con_cache_bust,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        )

        # Conexion con contexto SSL permisivo
        with urllib.request.urlopen(req, timeout=10, context=get_ssl_context()) as response:
            data = json.loads(response.read().decode('utf-8'))
            version_remota = data.get("version", "").strip()
            url_nuevo_exe = data.get("url")

        if version_remota and parse_version(version_remota) > parse_version(VERSION_ACTUAL):
            VentanaAvisoActualizacion(parent, version_remota, url_nuevo_exe)
        else:
            if manual:
                messagebox.showinfo(
                    "Sin actualizaciones", 
                    f"Ya tienes la version mas reciente (v{VERSION_ACTUAL}).",
                    parent=parent
                )

    except Exception as e:
        if manual:
            messagebox.showerror(
                "Error de conexion", 
                f"No se pudo comprobar el estado de actualizacion:\n{e}",
                parent=parent
            )


# --- GENERADOR DE PDF ---
class TicketPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format=(80, 220))
        self.set_auto_page_break(auto=True, margin=5)
        self.set_margins(4, 4, 4)

    def generar(self, es_factura, num_doc, emisor, cliente, items, base, total_iva, total, iva_desglose, ruta_salida):
        self.add_page()
        
        # 1. Logo
        if os.path.exists(LOGO_FILE):
            try:
                ancho_logo = 30
                x_centrado = (80 - ancho_logo) / 2
                self.image(LOGO_FILE, x=x_centrado, w=ancho_logo)
                self.ln(2)
            except Exception:
                pass

        # 2. Titulo y Fecha
        self.set_font("Helvetica", "B", 11)
        titulo = f"FACTURA SIMPLIFICADA: {num_doc}" if es_factura else f"TICKET DE VENTA: {num_doc}"
        self.multi_cell(72, 4.5, titulo, align='C')
        self.ln(1)
        
        self.set_font("Helvetica", "", 8)
        fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(72, 4, f"Fecha: {fecha_hora}", ln=True, align='C')
        self.ln(2)

        # 3. Emisor
        self.set_font("Helvetica", "B", 9)
        self.cell(72, 4.5, "DATOS DEL EMISOR", ln=True, border='B')
        self.set_font("Helvetica", "", 8.5)
        self.multi_cell(72, 4, emisor)
        self.ln(2)

        # 4. Cliente (en Factura)
        if es_factura and cliente.get("nombre"):
            self.set_font("Helvetica", "B", 9)
            self.cell(72, 4.5, "CLIENTE", ln=True, border='B')
            self.set_font("Helvetica", "", 8.5)
            info_cli = f"{cliente['nombre']}\nNIF/CIF: {cliente.get('nif', '')}\nDir: {cliente.get('domicilio', '')}"
            self.multi_cell(72, 4, info_cli)
            self.ln(2)

        # 5. Encabezado tabla
        self.set_font("Helvetica", "B", 8)
        self.cell(26, 4.5, "Articulo", border='TB')
        self.cell(10, 4.5, "Cant", border='TB', align='C')
        self.cell(14, 4.5, "Precio", border='TB', align='R')
        self.cell(8, 4.5, "IVA", border='TB', align='C')
        self.cell(14, 4.5, "Total", border='TB', align='R')
        self.ln(5.5)

        # 6. Filas de productos
        self.set_font("Helvetica", "", 8)
        for it in items:
            x_ini, y_ini = self.get_x(), self.get_y()
            self.multi_cell(26, 4, it['desc'])
            y_fin = self.get_y()
            
            self.set_xy(x_ini + 26, y_ini)
            self.cell(10, 4, f"{it['cant']:.1f}", align='C')
            self.cell(14, 4, f"{it['precio']:.2f}", align='R')
            self.cell(8, 4, f"{it['iva']}%", align='C')
            self.cell(14, 4, f"{it['total']:.2f}", align='R')
            self.set_y(max(y_fin, y_ini + 4.5))

        self.ln(2)
        self.line(4, self.get_y(), 76, self.get_y())
        self.ln(2)

        # 7. Totales
        self.set_font("Helvetica", "", 9)
        self.cell(42, 4.5, "Base Imponible:")
        self.cell(30, 4.5, f"{base:.2f} EUR", align='R', ln=True)
        self.cell(42, 4.5, "Cuota IVA:")
        self.cell(30, 4.5, f"{total_iva:.2f} EUR", align='R', ln=True)
            
        self.set_font("Helvetica", "B", 10)
        self.cell(42, 6, "TOTAL:")
        self.cell(30, 6, f"{total:.2f} EUR", align='R', ln=True)

        # 8. Desglose IVA
        if iva_desglose:
            self.set_font("Helvetica", "", 7.5)
            self.ln(1)
            for tipo, b in sorted(iva_desglose.items()):
                c = b * (tipo / 100)
                self.cell(72, 3.5, f"IVA {tipo}%: Base {b:.2f} EUR | Cuota {c:.2f} EUR", ln=True)

        self.ln(4)
        self.set_font("Helvetica", "I", 8)
        self.cell(72, 4, "Gracias por su visita", align='C', ln=True)
        self.output(ruta_salida)


# --- MODAL: GESTION DE CLIENTES ---
class GestionClientesModal(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Gestion de Clientes")
        self.geometry("620x390")
        self.grab_set()

        if os.path.exists(ICO_FILE):
            try:
                self.iconbitmap(ICO_FILE)
            except Exception:
                pass

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        frame_lista = ctk.CTkFrame(self)
        frame_lista.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_lista, text="Clientes Registrados", font=("Helvetica", 13, "bold")).pack(pady=5)
        self.scroll_lista = ctk.CTkScrollableFrame(frame_lista, width=250, height=270)
        self.scroll_lista.pack(fill="both", expand=True, padx=5, pady=5)

        frame_form = ctk.CTkFrame(self)
        frame_form.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_form, text="Datos del Cliente", font=("Helvetica", 13, "bold")).pack(pady=5)

        self.ent_nombre = ctk.CTkEntry(frame_form, placeholder_text="Nombre / Razon Social")
        self.ent_nombre.pack(fill="x", padx=10, pady=6)

        self.ent_nif = ctk.CTkEntry(frame_form, placeholder_text="NIF / CIF")
        self.ent_nif.pack(fill="x", padx=10, pady=6)

        self.ent_domicilio = ctk.CTkEntry(frame_form, placeholder_text="Domicilio Fiscal")
        self.ent_domicilio.pack(fill="x", padx=10, pady=6)

        self.cliente_idx_sel = None

        btn_add = ctk.CTkButton(frame_form, text="➕ Guardar / Actualizar", fg_color="#2b7a78", hover_color="#17252a", command=self.guardar_cliente)
        btn_add.pack(fill="x", padx=10, pady=(15, 5))

        btn_del = ctk.CTkButton(frame_form, text="🗑️ Eliminar Seleccionado", fg_color="#c62828", hover_color="#8e0000", command=self.eliminar_cliente)
        btn_del.pack(fill="x", padx=10, pady=5)

        btn_clear = ctk.CTkButton(frame_form, text="Limpiar Formulario", fg_color="gray40", hover_color="gray30", command=self.limpiar_form)
        btn_clear.pack(fill="x", padx=10, pady=5)

        self.recargar_lista()

    def recargar_lista(self):
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        for idx, cli in enumerate(self.master_app.clientes):
            btn = ctk.CTkButton(
                self.scroll_lista, 
                text=cli.get("nombre", "Sin nombre"), 
                anchor="w",
                fg_color="transparent", 
                hover_color=("gray75", "gray25"),
                text_color=("black", "white"),
                command=lambda i=idx: self.seleccionar_cliente(i)
            )
            btn.pack(fill="x", pady=2)

    def seleccionar_cliente(self, idx):
        self.cliente_idx_sel = idx
        cli = self.master_app.clientes[idx]
        self.ent_nombre.delete(0, "end")
        self.ent_nombre.insert(0, cli.get("nombre", ""))
        self.ent_nif.delete(0, "end")
        self.ent_nif.insert(0, cli.get("nif", ""))
        self.ent_domicilio.delete(0, "end")
        self.ent_domicilio.insert(0, cli.get("domicilio", ""))

    def guardar_cliente(self):
        nombre = self.ent_nombre.get().strip()
        nif = self.ent_nif.get().strip()
        domicilio = self.ent_domicilio.get().strip()

        if not nombre:
            messagebox.showwarning("Atencion", "El nombre es obligatorio.", parent=self)
            return

        nuevo_dato = {"nombre": nombre, "nif": nif, "domicilio": domicilio}

        if self.cliente_idx_sel is not None and 0 <= self.cliente_idx_sel < len(self.master_app.clientes):
            self.master_app.clientes[self.cliente_idx_sel] = nuevo_dato
        else:
            self.master_app.clientes.append(nuevo_dato)

        if guardar_json(CLIENTES_FILE, self.master_app.clientes):
            self.master_app.actualizar_combos()
            self.recargar_lista()
            self.limpiar_form()
            messagebox.showinfo("Exito", f"Cliente '{nombre}' guardado en clientes.json.", parent=self)

    def eliminar_cliente(self):
        if self.cliente_idx_sel is None or not (0 <= self.cliente_idx_sel < len(self.master_app.clientes)):
            messagebox.showwarning("Atencion", "Selecciona un cliente de la lista.", parent=self)
            return

        cli = self.master_app.clientes[self.cliente_idx_sel]
        if messagebox.askyesno("Confirmar", f"¿Eliminar al cliente '{cli['nombre']}'?", parent=self):
            del self.master_app.clientes[self.cliente_idx_sel]
            guardar_json(CLIENTES_FILE, self.master_app.clientes)
            self.master_app.actualizar_combos()
            self.recargar_lista()
            self.limpiar_form()

    def limpiar_form(self):
        self.cliente_idx_sel = None
        self.ent_nombre.delete(0, "end")
        self.ent_nif.delete(0, "end")
        self.ent_domicilio.delete(0, "end")


# --- MODAL: GESTION DE PRODUCTOS ---
class GestionProductosModal(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Gestion de Productos")
        self.geometry("620x390")
        self.grab_set()

        if os.path.exists(ICO_FILE):
            try:
                self.iconbitmap(ICO_FILE)
            except Exception:
                pass

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        frame_lista = ctk.CTkFrame(self)
        frame_lista.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_lista, text="Productos Registrados", font=("Helvetica", 13, "bold")).pack(pady=5)
        self.scroll_lista = ctk.CTkScrollableFrame(frame_lista, width=250, height=270)
        self.scroll_lista.pack(fill="both", expand=True, padx=5, pady=5)

        frame_form = ctk.CTkFrame(self)
        frame_form.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_form, text="Datos del Producto", font=("Helvetica", 13, "bold")).pack(pady=5)

        self.ent_desc = ctk.CTkEntry(frame_form, placeholder_text="Descripcion / Nombre")
        self.ent_desc.pack(fill="x", padx=10, pady=6)

        self.ent_precio = ctk.CTkEntry(frame_form, placeholder_text="Precio base (€)")
        self.ent_precio.pack(fill="x", padx=10, pady=6)

        self.ent_iva = ctk.CTkEntry(frame_form, placeholder_text="IVA % (ej: 10 o 21)")
        self.ent_iva.pack(fill="x", padx=10, pady=6)

        self.prod_idx_sel = None

        btn_add = ctk.CTkButton(frame_form, text="➕ Guardar / Actualizar", fg_color="#2b7a78", hover_color="#17252a", command=self.guardar_producto)
        btn_add.pack(fill="x", padx=10, pady=(15, 5))

        btn_del = ctk.CTkButton(frame_form, text="🗑️ Eliminar Seleccionado", fg_color="#c62828", hover_color="#8e0000", command=self.eliminar_producto)
        btn_del.pack(fill="x", padx=10, pady=5)

        btn_clear = ctk.CTkButton(frame_form, text="Limpiar Formulario", fg_color="gray40", hover_color="gray30", command=self.limpiar_form)
        btn_clear.pack(fill="x", padx=10, pady=5)

        self.recargar_lista()

    def recargar_lista(self):
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        for idx, prod in enumerate(self.master_app.productos):
            texto = f"{prod['desc']} ({prod['precio']:.2f}€ - {prod.get('iva', 10)}%)"
            btn = ctk.CTkButton(
                self.scroll_lista, 
                text=texto, 
                anchor="w",
                fg_color="transparent", 
                hover_color=("gray75", "gray25"),
                text_color=("black", "white"),
                command=lambda i=idx: self.seleccionar_producto(i)
            )
            btn.pack(fill="x", pady=2)

    def seleccionar_producto(self, idx):
        self.prod_idx_sel = idx
        p = self.master_app.productos[idx]
        self.ent_desc.delete(0, "end")
        self.ent_desc.insert(0, p.get("desc", ""))
        self.ent_precio.delete(0, "end")
        self.ent_precio.insert(0, str(p.get("precio", 0.0)))
        self.ent_iva.delete(0, "end")
        self.ent_iva.insert(0, str(p.get("iva", 10)))

    def guardar_producto(self):
        desc = self.ent_desc.get().strip()
        try:
            precio = float(self.entry_precio.get().strip().replace(',', '.'))
            iva = int(self.ent_iva.get().strip())
            if not desc or precio < 0 or iva < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Comprueba que la descripcion exista y que el precio e IVA sean validos.", parent=self)
            return

        nuevo_dato = {"desc": desc, "precio": precio, "iva": iva}

        if self.prod_idx_sel is not None and 0 <= self.prod_idx_sel < len(self.master_app.productos):
            self.master_app.productos[self.prod_idx_sel] = nuevo_dato
        else:
            self.master_app.productos.append(nuevo_dato)

        if guardar_json(PRODUCTOS_FILE, self.master_app.productos):
            self.master_app.actualizar_combos()
            self.recargar_lista()
            self.limpiar_form()
            messagebox.showinfo("Exito", f"Producto '{desc}' guardado en productos.json.", parent=self)

    def eliminar_producto(self):
        if self.prod_idx_sel is None or not (0 <= self.prod_idx_sel < len(self.master_app.productos)):
            messagebox.showwarning("Atencion", "Selecciona un producto de la lista.", parent=self)
            return

        prod = self.master_app.productos[self.prod_idx_sel]
        if messagebox.askyesno("Confirmar", f"¿Eliminar el producto '{prod['desc']}'?", parent=self):
            del self.master_app.productos[self.prod_idx_sel]
            guardar_json(PRODUCTOS_FILE, self.master_app.productos)
            self.master_app.actualizar_combos()
            self.recargar_lista()
            self.limpiar_form()

    def limpiar_form(self):
        self.prod_idx_sel = None
        self.ent_desc.delete(0, "end")
        self.ent_precio.delete(0, "end")
        self.ent_iva.delete(0, "end")


# --- APLICACION PRINCIPAL ---
class FacturadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Facturacion Obrador Belis - v{VERSION_ACTUAL}")
        self.geometry("1040x640")
        self.minsize(940, 560)

        # Aplicar icono a la ventana principal si existe
        if os.path.exists(ICO_FILE):
            try:
                self.iconbitmap(ICO_FILE)
            except Exception:
                pass

        # Cargar datos desde los archivos JSON
        self.clientes = cargar_json(CLIENTES_FILE, [{"nombre": "Cliente Mostrador", "nif": "", "domicilio": ""}])
        self.productos = cargar_json(PRODUCTOS_FILE, [
            {"desc": "Cafe con Leche", "precio": 1.50, "iva": 10},
            {"desc": "Tarta de Queso", "precio": 4.00, "iva": 10},
            {"desc": "Refresco", "precio": 2.00, "iva": 21}
        ])
        
        anio_actual = datetime.date.today().year
        self.config_data = cargar_json(CONFIG_FILE, {"ultimo_num": 0, "anio": anio_actual})
        if self.config_data.get("anio") != anio_actual:
            self.config_data = {"ultimo_num": 0, "anio": anio_actual}
            guardar_json(CONFIG_FILE, self.config_data)

        self.items_factura = []
        self.crear_interfaz()

        # Comprobar actualizaciones silenciosamente al inicio
        self.after(1000, lambda: comprobar_actualizacion(parent=self, manual=False))

    def get_num_factura(self):
        return f"{self.config_data['anio']}/{(self.config_data['ultimo_num'] + 1):03d}"

    def crear_interfaz(self):
        left_panel = ctk.CTkFrame(self, corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(left_panel, text="Opciones de Emision", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.var_es_factura = tk.BooleanVar(value=True)
        self.chk_tipo = ctk.CTkSwitch(
            left_panel, 
            text="Modo Factura (Desmarcar = Ticket)", 
            variable=self.var_es_factura, 
            command=self.on_tipo_change
        )
        self.chk_tipo.pack(pady=5, padx=15, anchor="w")

        ctk.CTkLabel(left_panel, text="Emisor:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(8, 0))
        self.txt_emisor = ctk.CTkTextbox(left_panel, height=75, width=260)
        self.txt_emisor.insert(
            "1.0", 
            "Obrador Belis (Belen Contrera Tubio)\n"
            "NIF: 28923218M\n"
            "Nº Reg. Sanitario: 41930-00511\n"
            "Domicilio: Avenida Aljarafe 43, Bormujos"
        )
        self.txt_emisor.pack(padx=15, pady=4)

        # Cliente + Gestion
        ctk.CTkLabel(left_panel, text="Cliente:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(8, 0))
        cli_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        cli_box.pack(fill="x", padx=15, pady=4)

        self.combo_clientes = ctk.CTkComboBox(cli_box, width=175)
        self.combo_clientes.pack(side="left", padx=(0, 5))

        btn_gest_cli = ctk.CTkButton(cli_box, text="⚙", width=35, command=self.abrir_gestion_clientes)
        btn_gest_cli.pack(side="left")

        # Producto + Gestion
        ctk.CTkLabel(left_panel, text="Añadir Producto:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        prod_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        prod_box.pack(fill="x", padx=15, pady=4)

        self.combo_productos = ctk.CTkComboBox(prod_box, width=175, command=self.auto_completar_producto)
        self.combo_productos.pack(side="left", padx=(0, 5))

        btn_gest_prod = ctk.CTkButton(prod_box, text="⚙", width=35, command=self.abrir_gestion_productos)
        btn_gest_prod.pack(side="left")

        row_inputs = ctk.CTkFrame(left_panel, fg_color="transparent")
        row_inputs.pack(fill="x", padx=15, pady=5)
        
        self.entry_cant = ctk.CTkEntry(row_inputs, placeholder_text="Cant", width=55)
        self.entry_cant.insert(0, "1")
        self.entry_cant.pack(side="left", padx=(0, 5))

        self.entry_precio = ctk.CTkEntry(row_inputs, placeholder_text="Precio", width=85)
        self.entry_precio.pack(side="left", padx=5)

        self.entry_iva = ctk.CTkEntry(row_inputs, placeholder_text="IVA%", width=65)
        self.entry_iva.pack(side="left", padx=5)

        btn_add = ctk.CTkButton(left_panel, text="+ Añadir a Lista", command=self.agregar_item, fg_color="#2b7a78", hover_color="#17252a")
        btn_add.pack(padx=15, pady=10, fill="x")

        # Boton para forzar comprobacion manual de actualizacion
        self.btn_check_update = ctk.CTkButton(
            left_panel,
            text="🔄 Buscar actualizaciones",
            font=("Helvetica", 11),
            fg_color="gray30",
            hover_color="gray20",
            height=28,
            command=lambda: comprobar_actualizacion(parent=self, manual=True)
        )
        self.btn_check_update.pack(side="bottom", padx=15, pady=(0, 15), fill="x")

        # Boton PDF Principal
        self.btn_pdf = ctk.CTkButton(
            left_panel, 
            text="Generar PDF", 
            font=("Helvetica", 14, "bold"),
            command=self.generar_documento, 
            height=40, 
            fg_color="#2e7d32", 
            hover_color="#1b5e20"
        )
        self.btn_pdf.pack(side="bottom", padx=15, pady=(10, 5), fill="x")

        # Panel Derecho
        right_panel = ctk.CTkFrame(self, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.lbl_num_doc = ctk.CTkLabel(right_panel, text=f"Documento actual: {self.get_num_factura()}", font=("Helvetica", 15, "bold"))
        self.lbl_num_doc.pack(pady=10)

        self.frame_items = ctk.CTkScrollableFrame(right_panel, label_text="Articulos del Documento")
        self.frame_items.pack(fill="both", expand=True, padx=10, pady=5)

        totales_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        totales_frame.pack(fill="x", padx=15, pady=10)

        self.lbl_totales = ctk.CTkLabel(totales_frame, text="Total: 0.00 €", font=("Helvetica", 16, "bold"))
        self.lbl_totales.pack(side="right")

        btn_borrar_todo = ctk.CTkButton(totales_frame, text="Limpiar Lista", width=90, fg_color="#c62828", hover_color="#8e0000", command=self.limpiar_items)
        btn_borrar_todo.pack(side="left")

        self.actualizar_combos()

    def abrir_gestion_clientes(self):
        GestionClientesModal(self)

    def abrir_gestion_productos(self):
        GestionProductosModal(self)

    def actualizar_combos(self):
        nombres_cli = [c["nombre"] for c in self.clientes] if self.clientes else [""]
        self.combo_clientes.configure(values=nombres_cli)
        if nombres_cli:
            self.combo_clientes.set(nombres_cli[0])

        nombres_prod = [p["desc"] for p in self.productos] if self.productos else [""]
        self.combo_productos.configure(values=nombres_prod)
        if nombres_prod:
            self.combo_productos.set(nombres_prod[0])
            self.auto_completar_producto(nombres_prod[0])

    def on_tipo_change(self):
        es_factura = self.var_es_factura.get()
        self.lbl_num_doc.configure(text=f"Documento: {self.get_num_factura() if es_factura else 'TICKET (Auto)'}")

    def auto_completar_producto(self, desc):
        prod = next((p for p in self.productos if p["desc"] == desc), None)
        if prod:
            self.entry_precio.delete(0, "end")
            self.entry_precio.insert(0, str(prod.get("precio", 0.0)))
            self.entry_iva.delete(0, "end")
            self.entry_iva.insert(0, str(prod.get("iva", 10)))

    def agregar_item(self):
        try:
            desc = self.combo_productos.get().strip()
            cant = float(self.entry_cant.get().strip().replace(',', '.'))
            precio = float(self.entry_precio.get().strip().replace(',', '.'))
            iva = int(self.entry_iva.get().strip())

            if not desc or cant <= 0 or precio < 0 or iva < 0:
                raise ValueError

            subtotal = cant * precio
            total = subtotal * (1 + iva / 100)

            existente = next((it for it in self.items_factura if it["desc"] == desc and it["precio"] == precio and it["iva"] == iva), None)
            if existente:
                existente["cant"] += cant
                existente["subtotal"] += subtotal
                existente["total"] += total
            else:
                self.items_factura.append({
                    "desc": desc, "cant": cant, "precio": precio, "iva": iva,
                    "subtotal": subtotal, "total": total
                })
            
            self.refrescar_tabla()
            self.entry_cant.delete(0, "end")
            self.entry_cant.insert(0, "1")
        except ValueError:
            messagebox.showerror("Error", "Comprueba que la cantidad, el precio y el IVA sean numeros validos.")

    def sumar_item(self, idx):
        if 0 <= idx < len(self.items_factura):
            it = self.items_factura[idx]
            it["cant"] += 1.0
            it["subtotal"] = it["cant"] * it["precio"]
            it["total"] = it["subtotal"] * (1 + it["iva"] / 100)
            self.refrescar_tabla()

    def restar_item(self, idx):
        if 0 <= idx < len(self.items_factura):
            it = self.items_factura[idx]
            if it["cant"] > 1:
                it["cant"] -= 1.0
                it["subtotal"] = it["cant"] * it["precio"]
                it["total"] = it["subtotal"] * (1 + it["iva"] / 100)
            else:
                del self.items_factura[idx]
            self.refrescar_tabla()

    def refrescar_tabla(self):
        for widget in self.frame_items.winfo_children():
            widget.destroy()

        base_total = sum(i["subtotal"] for i in self.items_factura)
        iva_total = sum(i["subtotal"] * (i["iva"] / 100) for i in self.items_factura)
        total_final = base_total + iva_total

        for idx, item in enumerate(self.items_factura):
            fila = ctk.CTkFrame(self.frame_items)
            fila.pack(fill="x", pady=2)
            
            lbl_desc = f"{item['cant']:.1f}x  {item['desc']} ({item['precio']:.2f}€ + {item['iva']}%)"
            btn_sumar_texto = ctk.CTkButton(
                fila,
                text=lbl_desc,
                anchor="w",
                fg_color="transparent", 
                hover_color=("gray80", "gray25"),
                text_color=("black", "white"),
                command=lambda i=idx: self.sumar_item(i)
            )
            btn_sumar_texto.pack(side="left", padx=5, fill="x", expand=True)

            btn_del = ctk.CTkButton(
                fila, text="X", width=26, height=24, 
                fg_color="#c62828", hover_color="#8e0000",
                command=lambda i=idx: self.eliminar_item(i)
            )
            btn_del.pack(side="right", padx=(3, 5))

            btn_mas = ctk.CTkButton(
                fila, text="+", width=26, height=24, 
                fg_color="#2e7d32", hover_color="#1b5e20",
                command=lambda i=idx: self.sumar_item(i)
            )
            btn_mas.pack(side="right", padx=3)

            btn_menos = ctk.CTkButton(
                fila, text="-", width=26, height=24, 
                fg_color="#ef6c00", hover_color="#b26a00",
                command=lambda i=idx: self.restar_item(i)
            )
            btn_menos.pack(side="right", padx=3)

            ctk.CTkLabel(
                fila, 
                text=f"{item['total']:.2f} €", 
                font=("Helvetica", 11, "bold")
            ).pack(side="right", padx=8)

        self.lbl_totales.configure(text=f"Total: {total_final:.2f} €  (Base: {base_total:.2f} € | IVA: {iva_total:.2f} €)")

    def eliminar_item(self, idx):
        if 0 <= idx < len(self.items_factura):
            del self.items_factura[idx]
            self.refrescar_tabla()

    def limpiar_items(self):
        self.items_factura.clear()
        self.refrescar_tabla()

    def generar_documento(self):
        if not self.items_factura:
            messagebox.showwarning("Atencion", "Añade al menos un producto a la lista.")
            return

        es_factura = self.var_es_factura.get()
        num_doc = self.get_num_factura() if es_factura else datetime.datetime.now().strftime("%H%M%S")
        emisor = self.txt_emisor.get("1.0", "end").strip()
        nombre_cli = self.combo_clientes.get()
        cliente_obj = next((c for c in self.clientes if c["nombre"] == nombre_cli), {"nombre": nombre_cli})

        base_total = sum(i["subtotal"] for i in self.items_factura)
        iva_total = sum(i["subtotal"] * (i["iva"] / 100) for i in self.items_factura)
        total_final = base_total + iva_total

        iva_grupos = {}
        for it in self.items_factura:
            iva_grupos[it["iva"]] = iva_grupos.get(it["iva"], 0) + it["subtotal"]

        nombre_salida = f"{'Factura' if es_factura else 'Ticket'}_{num_doc.replace('/', '_')}.pdf"
        ruta_salida = os.path.join(BASE_DIR, nombre_salida)

        try:
            pdf = TicketPDF()
            pdf.generar(es_factura, num_doc, emisor, cliente_obj, self.items_factura,
                        base_total, iva_total, total_final, iva_grupos, ruta_salida)

            if es_factura:
                self.config_data["ultimo_num"] += 1
                guardar_json(CONFIG_FILE, self.config_data)
                self.lbl_num_doc.configure(text=f"Documento actual: {self.get_num_factura()}")

            self.limpiar_items()
            messagebox.showinfo("Exito", f"Documento generado: {nombre_salida}")
            
            if sys.platform == "win32":
                os.startfile(ruta_salida)
            elif sys.platform.startswith("linux"):
                subprocess.call(["xdg-open", ruta_salida])
            elif sys.platform.darwin:
                subprocess.call(["open", ruta_salida])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF: {e}")


if __name__ == "__main__":
    app = FacturadorApp()
    app.mainloop()