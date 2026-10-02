import tkinter as tk
from tkinter import messagebox, ttk
from ttkthemes import ThemedTk 
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import datetime
import json
import os
import sys
import ctypes

if sys.platform == "win32":
    try:
        # Informa a Windows que la app es "consciente" del DPI
        # Esto evita el escalado borroso
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"Advertencia: No se pudo establecer la conciencia de DPI. {e}")

if getattr(sys, 'frozen', False):
    ASSET_PATH = sys._MEIPASS 
    DATA_PATH = os.path.dirname(sys.executable)
else:
    ASSET_PATH = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = ASSET_PATH

CLIENTES_FILE = os.path.join(DATA_PATH, 'clientes.json')
PRODUCTOS_FILE = os.path.join(DATA_PATH, 'productos.json')
CONFIG_FILE = os.path.join(DATA_PATH, 'config.json')

FONT_FILE = os.path.join(ASSET_PATH, 'DejaVuSans.ttf')
FONT_BOLD_FILE = os.path.join(ASSET_PATH, 'DejaVuSans-Bold.ttf')
FONT_ITALIC_FILE = os.path.join(ASSET_PATH, 'DejaVuSans-Oblique.ttf')


def load_data(filename, default_data):
    if not os.path.exists(filename):
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        save_data(filename, default_data)
        return default_data
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error de Archivo", f"El archivo {os.path.basename(filename)} tiene un formato inválido. Se cargan datos por defecto.")
            return default_data

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(orientation='P', unit='mm', format=(80, 1000), *args, **kwargs)
        try:
            self.add_font("DejaVu", "", FONT_FILE)
            self.add_font("DejaVu", "B", FONT_BOLD_FILE)
            self.add_font("DejaVu", "I", FONT_ITALIC_FILE)
            self.LOGO_PATH = os.path.join(ASSET_PATH, 'logo.png')
            self.LOGO_WIDTH = 30
            self.LOGO_HEIGHT = 30
        except Exception as e:
            pass
            
    def header(self):
        if os.path.exists(self.LOGO_PATH):
            x_centered = (80 - self.LOGO_WIDTH) / 2 
            self.image(self.LOGO_PATH, x=x_centered, y=3, w=self.LOGO_WIDTH, h=self.LOGO_HEIGHT)
            self.ln(self.LOGO_HEIGHT + 2)

    def footer(self):
        pass


class FacturadorApp(ThemedTk):
    def __init__(self):
        super().__init__(theme="yaru")
        self.title("Facturas Cafeteria Belis")
        
        self.clientes_default = [
            {"nombre": "Cliente Ejemplo S.A.", "nif": "B98765432", "domicilio": "Avenida Siempre Viva, 742"},
        ]
        self.productos_default = [
            {"desc": "Consultoría Técnica (hora)", "precio": 75.00, "iva": 21},
            {"desc": "Libros y Revistas", "precio": 10.00, "iva": 4},
        ]
        
        self.clientes_data = load_data(CLIENTES_FILE, self.clientes_default)
        self.productos_data = load_data(PRODUCTOS_FILE, self.productos_default)
        
        current_year = datetime.date.today().year
        config_default = {"last_invoice_number": 0, "current_year": current_year}
        self.config_data = load_data(CONFIG_FILE, config_default)

        if self.config_data.get('current_year') != current_year:
            self.config_data['current_year'] = current_year
            self.config_data['last_invoice_number'] = 0
            save_data(CONFIG_FILE, self.config_data)

        self.last_num = self.config_data['last_invoice_number']
        
        self.items_factura = []
        self.current_client_name = ""
        
        # --- NUEVO: Cargar la imagen del botón PDF ---
        try:
            pdf_icon_path = os.path.join(ASSET_PATH, 'pdf.png')
            pdf_icon_temp = tk.PhotoImage(file=pdf_icon_path)
            self.pdf_icon = pdf_icon_temp.subsample(8, 8)
            
        except tk.TclError:
            messagebox.showerror("Error de Carga", f"No se pudo encontrar o cargar la imagen 'pdf.png' en {ASSET_PATH}. Se usará texto.")
            self.pdf_icon = None 
        
        # --- AÑADIDO: Variable para controlar Factura/Ticket ---
        self.is_invoice_var = tk.BooleanVar(value=True) # Por defecto, marcamos como Factura
        
        self.build_ui()
        self.update_clientes_combo()
        self.update_productos_combo() 
        self.toggle_iva_input() # Inicializa el estado del campo IVA
        
    def get_next_invoice_number(self):
        next_num = self.last_num + 1
        return f"{self.config_data['current_year']}/{next_num:03d}"

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- ESTILOS MEJORADOS ---
        style = ttk.Style()
        
        main_font = ('DejaVu Sans', 9)
        bold_font = ('DejaVu Sans', 10, 'bold')
        
        style.configure("TLabelframe.Label", font=bold_font, foreground="#333")

        style.configure("Treeview", 
                        rowheight=25, 
                        font=main_font,
                        background=style.lookup("TFrame", "background")) 
        
        style.configure("Treeview.Heading", 
                        font=('DejaVu Sans', 10, 'bold'), 
                        background=style.lookup("TFrame", "background"),
                        foreground='black') 

        style.configure("TButton", 
                        font=main_font, 
                        padding=5)
        style.map("TButton",
                  background=[('active', "#000000")])

        style.configure("Accent.TButton", 
                        font=('DejaVu Sans', 9, 'bold'),
                        foreground='black',
                        background='#2196F3', 
                        padding=5)
        style.map("Accent.TButton",
                  background=[('active', '#1e88e5')])

        style.configure("Danger.TButton",
                        font=main_font,
                        foreground='black',
                        background='#f44336')
        style.map("Danger.TButton",
                  background=[('active', '#d32f2f')])

        style.configure("Fancy.TButton", 
                        foreground='white',
                        background='#4CAF50', 
                        padding=5)
        style.map("Fancy.TButton",
                  background=[('active', '#45a049')], 
                  foreground=[('active', 'black')])
        style.configure("CheckbuttonBold.TCheckbutton", 
                font=('DejaVu Sans', 9, 'bold'),
                padding=5)


        top_row_frame = ttk.Frame(main_frame)
        top_row_frame.pack(fill=tk.X, pady=5)
        
        left_column_frame = ttk.Frame(top_row_frame)
        left_column_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 5)) 

        general_frame = ttk.LabelFrame(left_column_frame, text="Datos Generales y Emisor", padding="5") 
        general_frame.pack(fill=tk.X, pady=5) 

        ttk.Label(general_frame, text="Nº Factura:", font=main_font).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.num_factura_var = tk.StringVar(value=self.get_next_invoice_number())
        self.entry_num_factura = ttk.Entry(general_frame, width=20, textvariable=self.num_factura_var, state='readonly', font=('DejaVu Sans', 9, 'bold')) 
        self.entry_num_factura.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(general_frame, text="Datos del Emisor (tu información):", font=main_font).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_emisor = tk.Text(general_frame, height=3, width=50, font=main_font)
        self.entry_emisor.grid(row=2, column=0, columnspan=2, padx=5, pady=2)
        self.entry_emisor.insert("1.0", "Obrador Belis S.L.\nNIF: B91942516\nDomicilio: Avenida Aljarafe, 43")

        receptor_frame = ttk.LabelFrame(left_column_frame, text="Datos del Cliente", padding="5") 
        receptor_frame.pack(fill=tk.X, pady=5) 

        ttk.Label(receptor_frame, text="Seleccionar Cliente:", font=main_font).grid(row=0, column=0, sticky="w", padx=5, pady=2, columnspan=2)
        
        self.cliente_seleccionado = tk.StringVar()
        self.combo_clientes = ttk.Combobox(receptor_frame, textvariable=self.cliente_seleccionado, width=40, state='readonly', font=main_font)
        self.combo_clientes.grid(row=1, column=0, sticky="w", padx=5, pady=2) 
        self.combo_clientes.bind('<<ComboboxSelected>>', self.show_selected_client_data)
        
        self.btn_gestion_clientes = ttk.Button(receptor_frame, text="Gestionar Clientes", command=self.open_client_manager) 
        self.btn_gestion_clientes.grid(row=1, column=1, padx=10, pady=2) 
        
        self.cliente_info_text = tk.Text(receptor_frame, height=3, width=60, state=tk.DISABLED, font=main_font)
        self.cliente_info_text.grid(row=2, column=0, columnspan=2, padx=5, pady=2) 
        
        # --- INPUT FRAME (MODIFICADO) ---
        items_input_frame = ttk.LabelFrame(top_row_frame, text="🍰 Añadir Producto 🍰", padding="5") 
        items_input_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0)) 

        self.input_fields = {}
        
        # --- NUEVA CASILLA DE VERIFICACIÓN ---
        self.check_is_invoice = ttk.Checkbutton(items_input_frame, 
                                        text="Marcar casilla si es FACTURA (con IVA). Desmarcar para TICKET (sin IVA).", 
                                        variable=self.is_invoice_var, 
                                        command=self.toggle_iva_input, 
                                        onvalue=True, 
                                        offvalue=False,
                                        style='CheckbuttonBold.TCheckbutton')
        self.check_is_invoice.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        # ------------------------------------
        
        ttk.Label(items_input_frame, text="Producto:", font=main_font).grid(row=1, column=0, sticky="w", padx=5)
        self.producto_seleccionado = tk.StringVar()
        combo = ttk.Combobox(items_input_frame, textvariable=self.producto_seleccionado, width=30, state='readonly', font='main_font')
        combo.grid(row=1, column=1, sticky="w", padx=5)
        combo.bind('<<ComboboxSelected>>', self.fill_price_on_product_select) 
        self.input_fields['combo_productos'] = combo
        
        ttk.Label(items_input_frame, text="Cantidad:", font=main_font).grid(row=2, column=0, sticky="w", padx=5)
        self.input_fields['cant'] = ttk.Entry(items_input_frame, width=10, font=main_font)
        self.input_fields['cant'].grid(row=2, column=1, sticky="w", padx=5)
        self.input_fields['cant'].insert(0, "1")
        
        ttk.Label(items_input_frame, text="Precio sin IVA:", font=main_font).grid(row=3, column=0, sticky="w", padx=5, pady=2) 
        self.input_fields['precio'] = ttk.Entry(items_input_frame, width=15, font=main_font)
        self.input_fields['precio'].grid(row=3, column=1, sticky="w", padx=5, pady=2) 
        
        ttk.Label(items_input_frame, text="IVA (%) a aplicar:", font=main_font).grid(row=4, column=0, sticky="w", padx=5, pady=2) 
        self.input_fields['iva_aplicar'] = ttk.Entry(items_input_frame, width=8, font=main_font)
        self.input_fields['iva_aplicar'].grid(row=4, column=1, sticky="w", padx=5, pady=2) 
        self.input_fields['iva_aplicar'].insert(0, "10") 
        
        ttk.Button(items_input_frame, text="Gestionar Tartas", command=self.open_product_manager).grid(row=5, column=0, padx=10, pady=5)
        
        self.btn_add_item = ttk.Button(items_input_frame, text="Añadir a la Factura", command=self.add_item_to_invoice, style='Accent.TButton') 
        self.btn_add_item.grid(row=6, column=0, columnspan=2, pady=15) 

        # --- RESTO DEL UI (SIN CAMBIOS EN TREEVIEW Y BOTONES) ---
        middle_row_frame = ttk.Frame(main_frame)
        middle_row_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        items_list_frame = ttk.LabelFrame(middle_row_frame, text="Detalle de la Factura", padding="5") 
        items_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5)) 

        tree_frame = ttk.Frame(items_list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("desc", "cant", "precio", "iva", "total"), show='headings', height=5)
        self.tree.heading("desc", text="Descripción")
        self.tree.heading("cant", text="Cant.")
        self.tree.heading("precio", text="Precio sin IVA")
        self.tree.heading("iva", text="IVA (%)")
        self.tree.heading("total", text="Total (IVA incl.)") 

        self.tree.column("desc", width=250, anchor=tk.W)
        self.tree.column("cant", width=70, anchor=tk.CENTER)
        self.tree.column("precio", width=140, anchor=tk.E)
        self.tree.column("iva", width=90, anchor=tk.CENTER)
        self.tree.column("total", width=155, anchor=tk.E)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind('<Delete>', self.delete_selected_item)
        
        tree_button_frame = ttk.Frame(items_list_frame)
        tree_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.btn_delete_item = ttk.Button(tree_button_frame, text="🗑️ Eliminar Ítem Seleccionado", command=lambda: self.delete_selected_item(event=None), style='Danger.TButton')
        self.btn_delete_item.pack(side=tk.LEFT, padx=5)

        footer_frame = ttk.LabelFrame(middle_row_frame, text="Totales", padding="10") 
        footer_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0)) 

        self.label_total = ttk.Label(footer_frame, text="Total: 0.00 €", font=('DejaVu Sans', 16, 'bold')) 
        self.label_total.pack(padx=10, pady=10) 
        
        if self.pdf_icon:
            self.btn_generate = ttk.Button(footer_frame, 
                                            image=self.pdf_icon, 
                                            command=self.generar_pdf_factura,
                                            style='Fancy.TButton')
        else:
            self.btn_generate = ttk.Button(footer_frame, 
                                            text="📄 GENERAR PDF ⬇️",
                                            command=self.generar_pdf_factura, 
                                            style='Fancy.TButton')
            
        self.btn_generate.pack(padx=10, pady=(0, 10)) 

        self.update_items_list()

    # --- NUEVO MÉTODO: Controla el estado del campo IVA ---
    def toggle_iva_input(self):
        """Habilita o deshabilita la entrada del IVA según si es factura o ticket."""
        # Habilitar temporalmente para que fill_price_on_product_select pueda modificarlo
        self.input_fields['iva_aplicar'].config(state='normal') 
        
        # Llamar a fill_price_on_product_select, que ajustará el valor y re-bloqueará si es necesario.
        self.fill_price_on_product_select() 
        

    def update_clientes_combo(self):
        nombres = [c['nombre'] for c in self.clientes_data]
        self.combo_clientes['values'] = nombres
        if nombres:
            self.cliente_seleccionado.set(nombres[0])
            self.current_client_name = nombres[0]
            self.show_selected_client_data()
        else:
            self.cliente_seleccionado.set("")
            self.current_client_name = ""
            self.show_selected_client_data(clear=True)

    def show_selected_client_data(self, event=None, clear=False):
        new_client_name = self.cliente_seleccionado.get()

        if new_client_name != self.current_client_name and self.items_factura:
            self.items_factura.clear()
            self.update_items_list()
            
        self.current_client_name = new_client_name
        
        self.cliente_info_text.config(state=tk.NORMAL)
        self.cliente_info_text.delete('1.0', tk.END)
        
        if clear or not self.cliente_seleccionado.get():
            self.cliente_info_text.config(state=tk.DISABLED)
            return

        nombre_sel = self.cliente_seleccionado.get()
        cliente = next((c for c in self.clientes_data if c['nombre'] == nombre_sel), None)
        
        if cliente:
            info = f"NIF/CIF: {cliente['nif']}\nDomicilio: {cliente['domicilio']}"
            self.cliente_info_text.insert(tk.END, info)
        
        self.cliente_info_text.config(state=tk.DISABLED)

    def open_client_manager(self):
        ClientManager(self)
        
    def update_productos_combo(self):
        productos_desc = [p['desc'] for p in self.productos_data]
        self.input_fields['combo_productos']['values'] = productos_desc
        if productos_desc:
            self.producto_seleccionado.set(productos_desc[0])
            self.fill_price_on_product_select()
        else:
            self.producto_seleccionado.set("")
            
    # --- MODIFICADO: Ajusta el valor del IVA al cambiar el producto/modo Factura/Ticket ---
    def fill_price_on_product_select(self, event=None):
        desc_sel = self.producto_seleccionado.get()
        producto = next((p for p in self.productos_data if p['desc'] == desc_sel), None)
        
        self.input_fields['precio'].delete(0, tk.END)
        self.input_fields['iva_aplicar'].config(state=tk.NORMAL) # Habilitar temporalmente
        self.input_fields['iva_aplicar'].delete(0, tk.END)
        
        if producto:
            self.input_fields['precio'].insert(0, str(producto['precio']))
            
            if self.is_invoice_var.get():
                # Modo Factura: Cargar IVA del producto
                self.input_fields['iva_aplicar'].insert(0, str(producto.get('iva', 10))) 
            else:
                # Modo Ticket: IVA a 0
                self.input_fields['iva_aplicar'].insert(0, "0")
        
        # Re-aplicar el bloqueo si está en modo Ticket
        if not self.is_invoice_var.get():
            self.input_fields['iva_aplicar'].config(state='readonly')
            
    def open_product_manager(self):
        ProductManager(self)

    def add_item_to_invoice(self):
        try:
            desc = self.producto_seleccionado.get()
            cant_nueva = float(self.input_fields['cant'].get())
            precio = float(self.input_fields['precio'].get())
            # El campo 'iva' contendrá 0 si la casilla Ticket está seleccionada
            iva = int(self.input_fields['iva_aplicar'].get()) 
            
            if not desc:
                raise ValueError("Selecciona un producto válido.")
            if cant_nueva <= 0 or precio <= 0 or iva < 0:
                raise ValueError("Cantidad, precio e IVA deben ser números válidos y positivos (o IVA cero).")

            subtotal_nuevo = cant_nueva * precio
            total_nuevo = subtotal_nuevo * (1 + iva / 100)
            item_existente = None

            for item in self.items_factura:
                # Comprueba si existe un ítem con la misma descripción, precio e IVA (para agrupar)
                if item['desc'] == desc and item['precio'] == precio and item['iva'] == iva:
                    item_existente = item
                    break

            if item_existente:
                item_existente['cant'] += cant_nueva
                item_existente['subtotal'] += subtotal_nuevo
                item_existente['total'] += total_nuevo
            else:
                self.items_factura.append({
                    "desc": desc,
                    "cant": cant_nueva,
                    "precio": precio,
                    "iva": iva, 
                    "subtotal": subtotal_nuevo,
                    "total": total_nuevo
                })
            
            self.update_items_list()
            
            self.input_fields['cant'].delete(0, tk.END)
            self.input_fields['cant'].insert(0, "1")
            
        except ValueError as e:
            messagebox.showerror("Error de Entrada", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al añadir item: {e}")

    def update_items_list(self, item_index_to_restore=None):
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        total_base = 0
        total_iva = 0
        
        new_item_ids = []

        for item in self.items_factura:
            item_id = self.tree.insert("", tk.END, values=(
                item['desc'],
                f"{item['cant']:.2f}",
                f"{item['precio']:.2f}",
                f"{item['iva']}%",
                f"{item['total']:.2f}"
            ))
            new_item_ids.append(item_id)

            total_base += item['subtotal']
            total_iva += item['subtotal'] * (item['iva'] / 100)

        total_final = total_base + total_iva
        
        self.label_total.config(text=f"Total: {total_final:.2f} € (Base: {total_base:.2f} € | IVA: {total_iva:.2f} €)")
        
        if item_index_to_restore is not None and item_index_to_restore < len(new_item_ids):
            item_to_select = new_item_ids[item_index_to_restore]
            self.tree.selection_set(item_to_select)
            self.tree.focus(item_to_select)

    def delete_selected_item(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona un ítem de la lista para ajustar.")
            return

        item_id = selected_items[0]
        item_index = self.tree.index(item_id)
        
        if 0 <= item_index < len(self.items_factura):
            item = self.items_factura[item_index]
            cantidad_actual = item['cant']
            precio_unitario = item['precio']

            if cantidad_actual > 1:
                item['cant'] = round(cantidad_actual - 1, 2)
                item['subtotal'] = round(item['cant'] * precio_unitario, 2)
                item['total'] = round(item['subtotal'] * (1 + item['iva'] / 100), 2)
            else:
                del self.items_factura[item_index]

        self.update_items_list(item_index_to_restore=item_index)
    
    # --- MODIFICADO: Lógica de generación de Factura/Ticket ---
    def generar_pdf_factura(self):
            try:
                es_factura_legal = self.is_invoice_var.get()
                
                if es_factura_legal:
                    numero = self.num_factura_var.get()
                    titulo_documento = f"Factura Simplificada: {numero}"
                else:
                    # Si es un ticket, el número es el timestamp
                    numero = datetime.datetime.now().strftime("%H%M%S") 
                    titulo_documento = f"TICKET de VENTA: {numero}"

                emisor = self.entry_emisor.get("1.0", tk.END).strip()
                
                nombre_cliente = self.cliente_seleccionado.get()
                cliente_info = self.cliente_info_text.get("1.0", tk.END).strip()
                receptor = f"{nombre_cliente}\n{cliente_info}"
                
                if not emisor or not nombre_cliente or not self.items_factura:
                    messagebox.showerror("Error", "Rellena datos, selecciona cliente y añade al menos un producto.")
                    return

                base_imponible = 0
                total_iva = 0
                iva_groups = {}
                
                for item in self.items_factura:
                    base_imponible += item['subtotal']
                    
                    iva_rate = item['iva']
                    cuota = item['subtotal'] * (iva_rate / 100)
                    total_iva += cuota

                    if iva_rate not in iva_groups:
                        iva_groups[iva_rate] = 0
                    iva_groups[iva_rate] += item['subtotal']

                total_final = base_imponible + total_iva
                fecha = datetime.date.today().strftime("%d/%m/%Y")
                
                pdf = PDF()
                pdf.alias_nb_pages()
                pdf.add_page()
                
                pdf.set_auto_page_break(True, margin=2)
                pdf.set_margin(2)

                # Título del Documento (Factura o Ticket)
                pdf.set_font('DejaVu', 'B', 8)
                pdf.cell(0, 3, titulo_documento, border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font('DejaVu', '', 8)
                pdf.cell(0, 3, f"Fecha: {fecha} | Hora: {datetime.datetime.now().strftime('%H:%M:%S')}", border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(2)

                pdf.set_font('DejaVu', 'B', 9)
                pdf.cell(0, 4, 'EMITIDO POR:', border='B', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font('DejaVu', '', 8)
                emisor_lines = emisor.split('\n')
                for line in emisor_lines:
                    pdf.multi_cell(0, 4, line, border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT) 
                pdf.ln(2)
                
                # Solo imprime datos del cliente si es Factura Legal o si hay datos
                if es_factura_legal & (len(nombre_cliente) > 0 and len(cliente_info) > 0):
                    pdf.set_font('DejaVu', 'B', 9)
                    pdf.cell(0, 4, 'CLIENTE:', border='B', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.set_font('DejaVu', '', 8)
                    receptor_lines = receptor.split('\n')
                    for line in receptor_lines:
                        if line.strip(): 
                            pdf.multi_cell(0, 4, line, border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.ln(2)

                pdf.set_font('DejaVu', 'B', 8)
                ancho_col = [20, 10, 13, 8, 17] 
                line_height_header = 5
                
                # Encabezados de tabla
                pdf.cell(ancho_col[0], line_height_header, 'Desc.', border='TB', align='L', new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.cell(ancho_col[1], line_height_header, 'Cant', border='TB', align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.cell(ancho_col[2], line_height_header, 'P.Base' if es_factura_legal else 'Precio', border='TB', align='R', new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.cell(ancho_col[3], line_height_header, 'IVA', border='TB', align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.cell(ancho_col[4], line_height_header, 'Total' if es_factura_legal else 'Importe', border='TB', align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT) 
                pdf.ln(1)

                pdf.set_font('DejaVu', '', 7)
                line_height = 4
                
                for item in self.items_factura:
                    desc = item['desc']
                    
                    # 1. Guardamos la posición X e Y actuales para el inicio de la fila
                    start_x = pdf.get_x() 
                    start_y = pdf.get_y()

                    # 2. Imprimimos la descripción usando multi_cell para permitir el *wrap* de texto
                    # La multi_cell automáticamente se posiciona en el margen izquierdo (x=2)
                    pdf.set_x(start_x)
                    pdf.multi_cell(ancho_col[0], line_height, desc, border=0, align='L', max_line_height=line_height)
                    
                    # 3. Guardamos la nueva posición Y (donde terminó la multi_cell)
                    end_y = pdf.get_y()

                    # 4. Reposicionamos el cursor para las columnas restantes:
                    #    X: Es la suma del X inicial (start_x) más el ancho de la columna de descripción (ancho_col[0])
                    #    Y: Es la Y inicial (start_y) para que se alineen horizontalmente con la primera línea de la descripción
                    pdf.set_xy(start_x + ancho_col[0], start_y) 
                    
                    # 5. Imprimimos las celdas restantes.
                    #    La altura de estas celdas sigue siendo 'line_height', pero forzamos el avance de línea (new_y=YPos.TOP)
                    #    para que el cursor no se mueva.

                    pdf.cell(ancho_col[1], line_height, f"{item['cant']:.2f}", border=0, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.cell(ancho_col[2], line_height, f"{item['precio']:.2f}€", border=0, align='R', new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.cell(ancho_col[3], line_height, f"{item['iva']}%", border=0, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.cell(ancho_col[4], line_height, f"{item['total']:.2f} €", border=0, align='R', new_x=XPos.LMARGIN, new_y=YPos.TOP)
                    
                    # 6. Finalmente, forzamos el cursor a la posición Y donde terminó la columna de descripción (end_y)
                    #    para que la siguiente fila de la tabla empiece correctamente.
                    pdf.set_y(end_y)
                    
                    pdf.ln(1)
                
                pdf.ln(2)
                
                pdf.set_font('DejaVu', 'B', 8)
                pdf.cell(0, 1, '', border='T', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                ANCHO_TEXTO_TOTAL = 51
                ANCHO_VALOR_TOTAL = 25
                
                # Desglose según sea Factura o Ticket
                if es_factura_legal:
                    pdf.set_font('DejaVu', '', 8)
                    pdf.cell(ANCHO_TEXTO_TOTAL, 4, "Base Imponible Total:", border=0, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.cell(ANCHO_VALOR_TOTAL, 4, f"{base_imponible:.2f} €", border=0, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                    pdf.cell(ANCHO_TEXTO_TOTAL, 4, "IVA Total:", border=0, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.cell(ANCHO_VALOR_TOTAL, 4, f"{total_iva:.2f} €", border=0, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                else:
                    pdf.set_font('DejaVu', '', 8)
                    pdf.cell(ANCHO_TEXTO_TOTAL, 4, "Subtotal:", border=0, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.cell(ANCHO_VALOR_TOTAL, 4, f"{total_final:.2f} €", border=0, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)


                pdf.set_font('DejaVu', 'B', 10)
                pdf.cell(0, 1, '', border='T', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(ANCHO_TEXTO_TOTAL, 6, "TOTAL A PAGAR:", border=0, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.cell(ANCHO_VALOR_TOTAL, 6, f"{total_final:.2f} €", border=0, align='R', fill=False, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 1, '', border='T', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(3)

                # Desglose de IVA solo si es Factura Legal
                if es_factura_legal:
                    pdf.set_font('DejaVu', 'B', 7)
                    pdf.cell(0, 3, 'Desglose de Tipos de IVA:', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.set_font('DejaVu', '', 7)
                    
                    for rate in sorted(iva_groups.keys()):
                        base = iva_groups[rate]
                        cuota = base * (rate / 100)
                        pdf.cell(0, 3, f"Base {rate}%: {base:.2f} € | Cuota: {cuota:.2f} €", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.ln(5)
                pdf.set_font('DejaVu', 'I', 7)
                pdf.cell(0, 3, 'Gracias por su confianza.', border=0, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(5)

                # Lógica de guardado de archivo y numeración
                nombre_limpio = nombre_cliente.replace(' ', '_').replace('.', '').replace(',', '')
                
                if es_factura_legal:
                    numero_limpio = numero.replace('/', '_')
                    nombre_fichero_base = f'Factura_{nombre_limpio}_{numero_limpio}.pdf'
                    
                    # Incrementa el número de factura
                    self.last_num += 1
                    self.config_data['last_invoice_number'] = self.last_num
                    save_data(CONFIG_FILE, self.config_data)
                    self.num_factura_var.set(self.get_next_invoice_number())
                else:
                    nombre_fichero_base = f'Ticket_{nombre_limpio}_{numero}.pdf'
                    
                
                nombre_archivo_salida = os.path.join(DATA_PATH, nombre_fichero_base)
                pdf.output(nombre_archivo_salida)
                
                # Limpiar la lista de items y el treeview
                self.items_factura.clear()
                self.update_items_list()
                
                messagebox.showinfo("Éxito", f"Documento '{os.path.basename(nombre_archivo_salida)}' generado correctamente en:\n{DATA_PATH}")
                try:
                    if sys.platform == "win32":
                        os.startfile(nombre_archivo_salida)
                    elif sys.platform.startswith("linux"):
                        import subprocess
                        subprocess.call(('xdg-open', nombre_archivo_salida))
                    elif sys.platform == "darwin":
                        import subprocess
                        subprocess.call(('open', nombre_archivo_salida))
                except Exception as e:
                    print(f"No se pudo abrir el archivo automáticamente: {e}")
            except ValueError as e:
                messagebox.showerror("Error de Cálculo", f"Error: {e}. Asegúrate de que los campos numéricos son correctos.")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error inesperado al generar el PDF: {e}")

class ClientManager(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Gestión de Clientes")
        self.transient(master) 
        self.grab_set() 
        self.resizable(False, False)
        
        self.clientes_data = master.clientes_data
        self.build_ui()
        self.load_client_list()

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(main_frame, padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(list_frame, text="Clientes Existentes:", font=('DejaVu Sans', 10, 'bold')).pack(pady=5)
        self.listbox = tk.Listbox(list_frame, height=10, width=50, font=('DejaVu Sans', 9),
                                    selectmode=tk.SINGLE, borderwidth=1, relief="solid")
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.select_client)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        form_frame = ttk.LabelFrame(main_frame, text="Detalles del Cliente", padding="10")
        form_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        ttk.Label(form_frame, text="Nombre/Razón Social:", font=('DejaVu Sans', 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_nombre = ttk.Entry(form_frame, width=30, font=('DejaVu Sans', 9))
        self.entry_nombre.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="NIF/CIF:", font=('DejaVu Sans', 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_nif = ttk.Entry(form_frame, width=30, font=('DejaVu Sans', 9))
        self.entry_nif.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Domicilio Fiscal:", font=('DejaVu Sans', 9)).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_domicilio = ttk.Entry(form_frame, width=30, font=('DejaVu Sans', 9))
        self.entry_domicilio.grid(row=2, column=1, pady=5)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="➕ Añadir Nuevo", command=self.add_client, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Guardar Cambios", command=self.update_client, style='TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.delete_client, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        
        self.selected_client_index = -1

    def load_client_list(self):
        self.listbox.delete(0, tk.END)
        for cliente in self.clientes_data:
            self.listbox.insert(tk.END, cliente['nombre'])
            
    def select_client(self, event):
        try:
            index = self.listbox.curselection()[0]
            self.selected_client_index = index
            cliente = self.clientes_data[index]
            
            self.entry_nombre.delete(0, tk.END)
            self.entry_nif.delete(0, tk.END)
            self.entry_domicilio.delete(0, tk.END)
            
            self.entry_nombre.insert(0, cliente['nombre'])
            self.entry_nif.insert(0, cliente['nif'])
            self.entry_domicilio.insert(0, cliente['domicilio'])
            
        except IndexError:
            pass
            
    def add_client(self):
        nombre = self.entry_nombre.get().strip()
        nif = self.entry_nif.get().strip()
        domicilio = self.entry_domicilio.get().strip()
        
        if not nombre or not nif:
            messagebox.showerror("Error", "El nombre y el NIF/CIF son obligatorios.")
            return

        self.entry_nombre.delete(0, tk.END)
        self.entry_nif.delete(0, tk.END)
        self.entry_domicilio.delete(0, tk.END)
        
        self.clientes_data.append({"nombre": nombre, "nif": nif, "domicilio": domicilio})
        save_data(CLIENTES_FILE, self.clientes_data)
        self.load_client_list()
        self.master.update_clientes_combo() 
        messagebox.showinfo("Añadido", f"Cliente '{nombre}' añadido con éxito.")

    def update_client(self):
        if self.selected_client_index == -1:
            messagebox.showerror("Error", "Selecciona un cliente para actualizar.")
            return
            
        nombre = self.entry_nombre.get().strip()
        nif = self.entry_nif.get().strip()
        domicilio = self.entry_domicilio.get().strip()
        
        if not nombre or not nif:
            messagebox.showerror("Error", "El nombre y el NIF/CIF son obligatorios.")
            return

        self.clientes_data[self.selected_client_index] = {"nombre": nombre, "nif": nif, "domicilio": domicilio}
        save_data(CLIENTES_FILE, self.clientes_data)
        self.load_client_list()
        self.master.update_clientes_combo()
        messagebox.showinfo("Actualizado", f"Cliente '{nombre}' actualizado con éxito.")

    def delete_client(self):
        if self.selected_client_index == -1:
            messagebox.showerror("Error", "Selecciona un cliente para eliminar.")
            return

        nombre = self.clientes_data[self.selected_client_index]['nombre']
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar a '{nombre}'?"):
            del self.clientes_data[self.selected_client_index]
            save_data(CLIENTES_FILE, self.clientes_data)
            self.load_client_list()
            self.master.update_clientes_combo()
            self.entry_nombre.delete(0, tk.END)
            self.entry_nif.delete(0, tk.END)
            self.entry_domicilio.delete(0, tk.END)
            self.selected_client_index = -1
            messagebox.showinfo("Eliminado", f"Cliente '{nombre}' eliminado.")

class ProductManager(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Gestión de Tartas")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        
        self.productos_data = master.productos_data
        self.build_ui()
        self.load_product_list()
        self.selected_product_index = -1

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(main_frame, padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(list_frame, text="Tartas Existentes:", font=('DejaVu Sans', 10, 'bold')).pack(pady=5)
        self.listbox = tk.Listbox(list_frame, height=10, width=50, font=('DejaVu Sans', 9),
                                    selectmode=tk.SINGLE, borderwidth=1, relief="solid")
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.select_product)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        form_frame = ttk.LabelFrame(main_frame, text="Detalles del Producto", padding="10")
        form_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        ttk.Label(form_frame, text="Descripción:", font=('DejaVu Sans', 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_desc = ttk.Entry(form_frame, width=30, font=('DejaVu Sans', 9))
        self.entry_desc.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Precio Base (€):", font=('DejaVu Sans', 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_precio = ttk.Entry(form_frame, width=30, font=('DejaVu Sans', 9))
        self.entry_precio.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="IVA (%):", font=('DejaVu Sans', 9)).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_iva = ttk.Entry(form_frame, width=30, font=('DejaVu Sans', 9))
        self.entry_iva.grid(row=2, column=1, pady=5)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="➕ Añadir Nuevo", command=self.add_product, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Guardar Cambios", command=self.update_product, style='TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.delete_product, style='Danger.TButton').pack(side=tk.LEFT, padx=5)

    def load_product_list(self):
        self.listbox.delete(0, tk.END)
        for producto in self.productos_data:
            self.listbox.insert(tk.END, f"{producto['desc']} ({producto['precio']:.2f} € | IVA: {producto['iva']}%)")
            
    def select_product(self, event):
        try:
            index = self.listbox.curselection()[0]
            self.selected_product_index = index
            producto = self.productos_data[index]
            
            self.entry_desc.delete(0, tk.END)
            self.entry_precio.delete(0, tk.END)
            self.entry_iva.delete(0, tk.END)
            
            self.entry_desc.insert(0, producto['desc'])
            self.entry_precio.insert(0, producto['precio'])
            self.entry_iva.insert(0, producto['iva']) 
            
        except IndexError:
            pass
            
    def add_product(self):
        desc = self.entry_desc.get().strip()
        try:
            precio = float(self.entry_precio.get().strip())
            iva = int(self.entry_iva.get().strip())
        except ValueError:
            messagebox.showerror("Error", "El precio y el IVA deben ser números válidos.")
            return

        if not desc or precio <= 0 or iva < 0:
            messagebox.showerror("Error", "La descripción, el precio y el IVA son obligatorios y válidos.")
            return

        self.entry_desc.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_iva.delete(0, tk.END)
        
        self.productos_data.append({"desc": desc, "precio": precio, "iva": iva})
        save_data(PRODUCTOS_FILE, self.productos_data)
        self.load_product_list()
        self.master.update_productos_combo()
        messagebox.showinfo("Añadido", f"Producto '{desc}' añadido con éxito.")

    def update_product(self):
        if self.selected_product_index == -1:
            messagebox.showerror("Error", "Selecciona un producto para actualizar.")
            return
            
        desc = self.entry_desc.get().strip()
        try:
            precio = float(self.entry_precio.get().strip())
            iva = int(self.entry_iva.get().strip())
        except ValueError:
            messagebox.showerror("Error", "El precio y el IVA deben ser números válidos.")
            return
        
        if not desc or precio <= 0 or iva < 0:
            messagebox.showerror("Error", "La descripción, el precio y el IVA son obligatorios y válidos.")
            return

        self.productos_data[self.selected_product_index] = {"desc": desc, "precio": precio, "iva": iva}
        save_data(PRODUCTOS_FILE, self.productos_data)
        self.load_product_list()
        self.master.update_productos_combo()
        messagebox.showinfo("Actualizado", f"Producto '{desc}' actualizado con éxito.")

    def delete_product(self):
        if self.selected_product_index == -1:
            messagebox.showerror("Error", "Selecciona un producto para eliminar.")
            return

        desc = self.productos_data[self.selected_product_index]['desc']
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar el producto '{desc}'?"):
            del self.productos_data[self.selected_product_index]
            save_data(PRODUCTOS_FILE, self.productos_data)
            self.load_product_list()
            self.master.update_productos_combo()
            self.entry_desc.delete(0, tk.END)
            self.entry_precio.delete(0, tk.END)
            self.selected_product_index = -1
            messagebox.showinfo("Eliminado", f"Producto '{desc}' eliminado.")


if __name__ == "__main__":
    app = FacturadorApp()
    app.mainloop()