#!/usr/bin/env python3
"""
Smart File Organizer GUI - Professional Windows interface
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add src to path to import organizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from organizer import SmartFileOrganizer


class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Creates a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # No window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", 8, "normal"))
        label.pack(ipadx=1)
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class SettingsManager:
    """Manage user settings (last folder, config path)"""
    def __init__(self):
        self.settings_file = Path.home() / ".smart_file_organizer_settings.json"
        self.settings = self.load_settings()
    
    def load_settings(self):
        default_settings = {
            "last_folder": "",
            "last_config": "",
            "window_geometry": "700x500"
        }
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return default_settings
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass  # Fail silently
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value


class OrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Organizer - Organização Inteligente de Arquivos")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)
        
        # Settings
        self.settings = SettingsManager()
        
        # Variables
        self.target_folder = tk.StringVar(value=self.settings.get("last_folder", ""))
        self.dry_run = tk.BooleanVar(value=True)  # Default to dry-run
        self.apply_changes = tk.BooleanVar(value=False)
        self.config_path = tk.StringVar(value=self.settings.get("last_config", ""))
        self.is_processing = False
        
        # Create UI
        self.create_widgets()
        self.setup_layout()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header()
        
        # Content pane (two panels)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel - Controls
        self.left_panel = ttk.LabelFrame(self.content_frame, text="Configuração", padding="15")
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right panel - Log
        self.right_panel = ttk.LabelFrame(self.content_frame, text="Log de Operações", padding="15")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Build left panel (controls)
        self.build_controls()
        
        # Build right panel (log)
        self.build_log_panel()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_label = ttk.Label(header_frame, text="Smart File Organizer", 
                               font=("Segoe UI", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Description
        desc_label = ttk.Label(header_frame, 
                              text="Organiza arquivos por conteúdo semântico, não apenas por extensão",
                              font=("Segoe UI", 9), foreground="#666666")
        desc_label.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))
    
    def build_controls(self):
        # Folder selection
        folder_frame = ttk.Frame(self.left_panel)
        folder_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(folder_frame, text="Pasta para organizar:").pack(anchor=tk.W)
        
        folder_input_frame = ttk.Frame(folder_frame)
        folder_input_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.folder_entry = ttk.Entry(folder_input_frame, textvariable=self.target_folder, 
                                     font=("Segoe UI", 9))
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(folder_input_frame, text="Procurar...", 
                               command=self.browse_folder, width=10)
        browse_btn.pack(side=tk.RIGHT)
        
        ToolTip(browse_btn, "Selecione a pasta que você deseja organizar")
        
        # Config file
        config_frame = ttk.Frame(self.left_panel)
        config_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(config_frame, text="Arquivo de config (opcional):").pack(anchor=tk.W)
        
        config_input_frame = ttk.Frame(config_frame)
        config_input_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.config_entry = ttk.Entry(config_input_frame, textvariable=self.config_path,
                                     font=("Segoe UI", 9))
        self.config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        config_browse_btn = ttk.Button(config_input_frame, text="Procurar...", 
                                      command=self.browse_config, width=10)
        config_browse_btn.pack(side=tk.RIGHT)
        
        ToolTip(config_browse_btn, "Selecione um arquivo JSON de configuração personalizado")
        
        # Options
        options_frame = ttk.LabelFrame(self.left_panel, text="Opções de Execução", padding="12")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Dry-run option
        dry_run_frame = ttk.Frame(options_frame)
        dry_run_frame.pack(fill=tk.X, pady=2)
        
        self.dry_run_check = ttk.Checkbutton(dry_run_frame, text="🔍 Modo de teste (dry-run)", 
                                           variable=self.dry_run, command=self.on_dry_run_change)
        self.dry_run_check.pack(anchor=tk.W)
        
        dry_run_desc = ttk.Label(dry_run_frame, 
                                text="Mostra o que seria feito SEM mover arquivos (padrão seguro)",
                                font=("Segoe UI", 8), foreground="#666666")
        dry_run_desc.pack(anchor=tk.W, padx=(20, 0))
        
        # Apply changes option
        apply_frame = ttk.Frame(options_frame)
        apply_frame.pack(fill=tk.X, pady=2)
        
        self.apply_check = ttk.Checkbutton(apply_frame, text="⚡ Aplicar mudanças (MOVE arquivos)", 
                                         variable=self.apply_changes, command=self.on_apply_change)
        self.apply_check.pack(anchor=tk.W)
        
        apply_desc = ttk.Label(apply_frame, 
                              text="ATENÇÃO: Move arquivos para as pastas de categoria",
                              font=("Segoe UI", 8), foreground="#cc0000")
        apply_desc.pack(anchor=tk.W, padx=(20, 0))
        
        # Action buttons
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Configure button styles
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"))
        
        self.start_button = ttk.Button(button_frame, text="▶ Iniciar Organização", 
                                      command=self.start_organization, style="Accent.TButton",
                                      width=18)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.plan_button = ttk.Button(button_frame, text="📋 Ver Plano", 
                                     command=self.show_plan, width=12)
        self.plan_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🗑 Limpar Log", 
                  command=self.clear_log, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📂 Abrir Pasta", 
                  command=self.open_target_folder, width=12).pack(side=tk.LEFT, padx=5)
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(self.left_panel)
        self.progress_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Processando...")
        self.progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(2, 0))
        self.progress_frame.pack_forget()  # Hide initially
    
    def build_log_panel(self):
        # Log text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(self.right_panel, wrap=tk.WORD, 
                                                 font=("Consolas", 9),
                                                 background="#f8f8f8",
                                                 relief=tk.SOLID, borderwidth=1)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for coloring
        self.log_text.tag_configure("info", foreground="#0066cc")
        self.log_text.tag_configure("success", foreground="#009900")
        self.log_text.tag_configure("warning", foreground="#ff6600")
        self.log_text.tag_configure("error", foreground="#cc0000")
        self.log_text.tag_configure("header", foreground="#000000", font=("Consolas", 9, "bold"))
    
    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_layout(self):
        # Configure grid weights for resizing
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        self.left_panel.columnconfigure(0, weight=1)
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=1)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta para organizar",
                                        initialdir=self.target_folder.get() or os.path.expanduser("~"))
        if folder:
            self.target_folder.set(folder)
            self.settings.set("last_folder", folder)
            self.log_message(f"📁 Pasta selecionada: {folder}", "info")
    
    def browse_config(self):
        config = filedialog.askopenfilename(
            title="Selecione o arquivo de configuração",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.config_path.get()) if self.config_path.get() else os.path.expanduser("~")
        )
        if config:
            self.config_path.set(config)
            self.settings.set("last_config", config)
            self.log_message(f"⚙️ Configuração carregada: {config}", "info")
    
    def on_dry_run_change(self):
        if self.dry_run.get():
            self.apply_changes.set(False)
            self.log_message("🔒 Modo dry-run ativado (padrão seguro)", "info")
    
    def on_apply_change(self):
        if self.apply_changes.get():
            self.dry_run.set(False)
            self.log_message("⚠️ Modo de aplicação ativado - ARQUIVOS SERÃO MOVIDOS!", "warning")
    
    def log_message(self, message, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.insert(tk.END, formatted_message + "\n", tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log_message("🗑 Log limpo", "info")
    
    def open_target_folder(self):
        folder = self.target_folder.get()
        if folder and os.path.exists(folder):
            # Open folder in file explorer (Windows)
            if os.name == 'nt':  # Windows
                os.startfile(folder)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', folder])
            self.log_message(f"📂 Abrindo pasta: {folder}", "info")
        elif not folder:
            messagebox.showwarning("Atenção", "Nenhuma pasta selecionada")
        else:
            messagebox.showerror("Erro", "A pasta selecionada não existe")
    
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def set_processing(self, processing):
        self.is_processing = processing
        if processing:
            self.start_button.config(state="disabled")
            self.plan_button.config(state="disabled")
            self.progress_frame.pack(fill=tk.X, pady=(15, 0), before=self.left_panel.winfo_children()[-1])
            self.progress_bar.start(10)
            self.update_status("Processando...")
        else:
            self.start_button.config(state="normal")
            self.plan_button.config(state="normal")
            self.progress_bar.stop()
            self.progress_frame.pack_forget()
            self.update_status("Pronto")
    
    def start_organization(self):
        if self.is_processing:
            return
        
        target = self.target_folder.get().strip()
        if not target:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta para organizar.")
            return
        
        if not os.path.exists(target):
            messagebox.showerror("Erro", "A pasta selecionada não existe.")
            return
        
        # Validate options
        if self.dry_run.get() and self.apply_changes.get():
            messagebox.showwarning("Aviso", "Modo de teste e aplicar mudanças são mutuamente exclusivos. Desativando aplicar mudanças.")
            self.apply_changes.set(False)
        
        # Disable UI during processing
        self.set_processing(True)
        self.clear_log()
        self.log_message(f"🚀 Iniciando organização de: {target}", "header")
        self.log_message(f"📋 Modo: {'Dry-run (apenas visualização)' if self.dry_run.get() else 'Aplicar mudanças'}", "info")
        if self.config_path.get().strip():
            self.log_message(f"⚙️ Usando configuração: {self.config_path.get()}", "info")
        
        # Run in background thread
        thread = threading.Thread(target=self.run_organization, args=(target,))
        thread.daemon = True
        thread.start()
    
    def run_organization(self, target):
        try:
            # Prepare arguments for organizer
            args = []
            if not self.dry_run.get():  # If not dry-run, we want to apply
                args.append("--apply")
            if self.config_path.get().strip():
                args.extend(["--config", self.config_path.get().strip()])
            args.append(target)
            
            # Import and run main
            from src.organizer import main
            # We need to simulate sys.argv
            old_argv = sys.argv
            sys.argv = ['smart_organize.py'] + args
            
            try:
                main()
                self.log_message("✅ Organização concluída com sucesso!", "success")
            finally:
                sys.argv = old_argv
                
        except Exception as e:
            self.log_message(f"❌ Erro durante a organização: {str(e)}", "error")
            import traceback
            self.log_message(traceback.format_exc(), "error")
        finally:
            self.set_processing(False)
    
    def show_plan(self):
        if self.is_processing:
            messagebox.showwarning("Aguarde", "Aguarde a conclusão da operação atual.")
            return
        
        target = self.target_folder.get().strip()
        if not target:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta primeiro.")
            return
        
        if not os.path.exists(target):
            messagebox.showerror("Erro", "A pasta selecionada não existe.")
            return
        
        self.set_processing(True)
        self.clear_log()
        self.log_message("📋 Gerando plano de organização (modo dry-run)...", "header")
        
        thread = threading.Thread(target=self.run_plan, args=(target,))
        thread.daemon = True
        thread.start()
    
    def run_plan(self, target):
        try:
            # Always run dry-run for plan (don't use --apply)
            args = []
            if self.config_path.get().strip():
                args.extend(["--config", self.config_path.get().strip()])
            args.append(target)
            
            from src.organizer import main
            old_argv = sys.argv
            sys.argv = ['smart_organize.py'] + args
            
            try:
                main()
                self.log_message("📋 Plano gerado acima. Revise cuidadosamente antes de aplicar mudanças.", "info")
            finally:
                sys.argv = old_argv
                
        except Exception as e:
            self.log_message(f"❌ Erro ao gerar plano: {str(e)}", "error")
            import traceback
            self.log_message(traceback.format_exc(), "error")
        finally:
            self.set_processing(False)
    
    def on_closing(self):
        # Save settings before closing
        self.settings.set("last_folder", self.target_folder.get())
        self.settings.set("last_config", self.config_path.get())
        self.settings.save_settings()
        self.root.destroy()


def main():
    root = tk.Tk()
    # Try to set a modern theme if available
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "xpnative" in style.theme_names():
            style.theme_use("xpnative")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except:
        pass  # Use default theme if custom themes fail
    
    app = OrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()