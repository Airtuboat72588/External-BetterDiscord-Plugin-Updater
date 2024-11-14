import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import requests
import os
import re
import json

class PluginManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Actualizador de Plugins")
        
        self.config_file = "config.json"
        self.plugins_folder = self.load_config()
        
        if not self.plugins_folder:
            self.plugins_folder = self.select_plugins_folder()
            self.save_config(self.plugins_folder)
        
        self.plugin_files = [f for f in os.listdir(self.plugins_folder) if f.endswith('.js')]
        
        tk.Label(root, text="Plugins:").grid(row=0, column=0, padx=10, pady=10)
        
        self.plugin_list = scrolledtext.ScrolledText(root, width=50, height=10)
        self.plugin_list.grid(row=1, column=0, padx=10, pady=10)
        self.plugin_list.insert(tk.END, "\n".join(self.plugin_files))
        
        tk.Button(root, text="Comprobar Actualizaciones", command=self.check_for_updates).grid(row=2, column=0, pady=10)
        
        self.update_frame = tk.Frame(root)
        self.update_frame.grid(row=3, column=0, padx=10, pady=10)
        
        self.update_list = scrolledtext.ScrolledText(self.update_frame, width=50, height=10)
        self.update_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.update_button = tk.Button(self.update_frame, text="Actualizar Plugins Seleccionados", command=self.update_selected_plugins)
        self.update_button.pack(side=tk.BOTTOM, pady=10)
        
        self.update_checkboxes = {}
        
        tk.Label(root, text="Progreso:").grid(row=4, column=0, padx=10, pady=10)
        
        self.progress_output = scrolledtext.ScrolledText(root, width=50, height=10)
        self.progress_output.grid(row=5, column=0, padx=10, pady=10)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as file:
                config = json.load(file)
                return config.get("plugins_folder")
        return None
    
    def save_config(self, plugins_folder):
        with open(self.config_file, 'w', encoding='utf-8') as file:
            json.dump({"plugins_folder": plugins_folder}, file)
    
    def select_plugins_folder(self):
        folder_selected = filedialog.askdirectory(title="Seleccionar Carpeta de Plugins")
        if not folder_selected:
            messagebox.showerror("Error", "Debe seleccionar una carpeta para continuar.")
            self.root.quit()
        return folder_selected
    
    def get_plugin_info(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        name_match = re.search(r'\* @name (.+)', content)
        version_match = re.search(r'\* @version (.+)', content)
        update_url_match = re.search(r'\* @updateUrl (.+)', content)
        
        if not name_match or not version_match or not update_url_match:
            raise ValueError(f"Falta metadata requerida en {file_path}")
        
        name = name_match.group(1)
        version = version_match.group(1)
        update_url = update_url_match.group(1)
        
        return name, version, update_url
    
    def check_for_updates(self):
        self.plugin_list.delete('1.0', tk.END)
        self.update_list.delete('1.0', tk.END)
        self.update_checkboxes.clear()
        self.progress_output.delete('1.0', tk.END)
        
        for plugin_file in self.plugin_files:
            plugin_path = os.path.join(self.plugins_folder, plugin_file)
            try:
                name, local_version, update_url = self.get_plugin_info(plugin_path)
                
                response = requests.get(update_url)
                response.raise_for_status()
                
                remote_version = re.search(r'\* @version (.+)', response.text).group(1)
                
                if self.is_newer_version(remote_version, local_version):
                    self.progress_output.insert(tk.END, f"{plugin_file} - Actualización disponible\n", 'naranja')
                    self.add_update_checkbox(plugin_file, name, remote_version, update_url)
                    self.plugin_list.insert(tk.END, f"{plugin_file} : Actualización disponible\n")
                else:
                    self.progress_output.insert(tk.END, f"{plugin_file} - Actualizado\n", 'verde')
                self.plugin_list.insert(tk.END, f"{plugin_file} : Actualizado\n")
            except (requests.RequestException, ValueError) as e:
                self.progress_output.insert(tk.END, f"{plugin_file} - Error: {e}\n", 'rojo')
                self.plugin_list.insert(tk.END, f"{plugin_file} : Error\n")
        
        self.progress_output.tag_config('verde', foreground='green')
        self.progress_output.tag_config('naranja', foreground='orange')
        self.progress_output.tag_config('rojo', foreground='red')
    
    def add_update_checkbox(self, plugin_file, name, remote_version, update_url):
        var = tk.BooleanVar()
        checkbox = tk.Checkbutton(self.update_list, text=f"{name} (v{remote_version})", variable=var)
        checkbox.pack(anchor='w')
        self.update_checkboxes[plugin_file] = (var, update_url)
    
    def update_selected_plugins(self):
        for plugin_file, (var, update_url) in self.update_checkboxes.items():
            if var.get():
                plugin_path = os.path.join(self.plugins_folder, plugin_file)
                try:
                    response = requests.get(update_url)
                    response.raise_for_status()
                    self.update_plugin(plugin_path, response.text)
                    messagebox.showinfo("Actualización", f"Plugin '{plugin_file}' actualizado correctamente")
                except requests.RequestException as e:
                    messagebox.showerror("Error", f"Error al actualizar el plugin '{plugin_file}': {e}")
    
    def is_newer_version(self, remote_version, local_version):
        return tuple(map(int, remote_version.split('.'))) > tuple(map(int, local_version.split('.')))
    
    def update_plugin(self, plugin_path, new_content):
        with open(plugin_path, 'w', encoding='utf-8') as file:
            file.write(new_content)

if __name__ == "__main__":
    root = tk.Tk()
    app = PluginManager(root)
    root.mainloop()