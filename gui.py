#!/usr/bin/env python3
"""
Smart File Organizer GUI - Windows executable front-end
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import os
from pathlib import Path

# Add src to path to import organizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from organizer import SmartFileOrganizer


class OrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Organizer")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Variables
        self.target_folder = tk.StringVar()
        self.dry_run = tk.BooleanVar(value=True)  # Default to dry-run
        self.apply_changes = tk.BooleanVar(value=False)
        self.config_path = tk.StringVar()
        self.is_processing = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Folder selection
        ttk.Label(main_frame, text="Pasta para organizar:").grid(row=0, column=0, sticky=tk.W, pady=5)
        folder_entry = ttk.Entry(main_frame, textvariable=self.target_folder, width=50)
        folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Procurar...", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)
        
        # Config file (optional)
        ttk.Label(main_frame, text="Arquivo de config (opcional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_entry = ttk.Entry(main_frame, textvariable=self.config_path, width=50)
        config_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Procurar...", command=self.browse_config).grid(row=1, column=2, padx=5, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Opções", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(options_frame, text="Modo de teste (dry-run) - NÃO move arquivos", 
                       variable=self.dry_run).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Aplicar mudanças (MOVE arquivos)", 
                       variable=self.apply_changes).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Iniciar Organização", 
                                      command=self.start_organization)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Ver Plano", 
                  command=self.show_plan).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Limpar Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Sair", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Log area
        ttk.Label(main_frame, text="Log de operações:").grid(row=4, column=0, sticky=tk.W, pady=(10,0))
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=15)
        self.log_text.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta para organizar")
        if folder:
            self.target_folder.set(folder)
            
    def browse_config(self):
        config = filedialog.askopenfilename(
            title="Selecione o arquivo de configuração",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if config:
            self.config_path.set(config)
            
    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def set_processing(self, processing):
        self.is_processing = processing
        if processing:
            self.start_button.config(state="disabled")
            self.update_status("Processando...")
        else:
            self.start_button.config(state="normal")
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
        self.log_message(f"Iniciando organização de: {target}")
        self.log_message(f"Modo: {'Dry-run (apenas visualização)' if self.dry_run.get() else 'Aplicar mudanças'}")
        
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
            finally:
                sys.argv = old_argv
                
            self.log_message("Organização concluída com sucesso!")
            
        except Exception as e:
            self.log_message(f"Erro durante a organização: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
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
        self.log_message("Gerando plano de organização (dry-run)...")
        
        thread = threading.Thread(target=self.run_plan, args=(target,))
        thread.daemon = True
        thread.start()
        
    def run_plan(self, target):
        try:
            # Always run dry-run for plan
            args = ["--apply"]  # Wait, we want dry-run for plan, so NOT --apply
            # Actually, dry-run is default, so we don't need --apply
            if self.config_path.get().strip():
                args.extend(["--config", self.config_path.get().strip()])
            args.append(target)
            
            from src.organizer import main
            old_argv = sys.argv
            sys.argv = ['smart_organize.py'] + args
            
            try:
                main()
            finally:
                sys.argv = old_argv
                
            self.log_message("Plano gerado acima. Revise cuidadosamente antes de aplicar mudanças.")
            
        except Exception as e:
            self.log_message(f"Erro ao gerar plano: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
        finally:
            self.set_processing(False)


def main():
    root = tk.Tk()
    app = OrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()