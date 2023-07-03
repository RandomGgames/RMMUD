import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class MyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("My GUI")
        
        # Create toolbar
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side="top", fill="x")
        
        # Create toolbar buttons
        self.settings_btn = ttk.Button(self.toolbar, text="Settings", command=self.open_settings)
        self.settings_btn.pack(side="left")
        
        self.about_btn = ttk.Button(self.toolbar, text="About", command=self.show_about)
        self.about_btn.pack(side="left")
        
        self.help_btn = ttk.Button(self.toolbar, text="Help", command=self.open_help)
        self.help_btn.pack(side="left")
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief="sunken")
        self.status_bar.pack(side="bottom", fill="x")
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        
        # Add settings widgets
        update_checkbox = ttk.Checkbutton(settings_window, text="Check for updates")
        update_checkbox.pack()
        
        logging_label = ttk.Label(settings_window, text="Logging level:")
        logging_label.pack()
        
        logging_combo = ttk.Combobox(settings_window, values=["Debug", "Info", "Warning", "Error"])
        logging_combo.pack()
        
        downloads_label = ttk.Label(settings_window, text="Downloads location:")
        downloads_label.pack()
        
        downloads_entry = ttk.Entry(settings_window)
        downloads_entry.pack()
        
        api_key_label = ttk.Label(settings_window, text="API Key:")
        api_key_label.pack()
        
        api_key_entry = ttk.Entry(settings_window, show="*")  # Entry field with obscured text
        api_key_entry.pack()
        
        show_api_key_btn = ttk.Button(settings_window, text="Show API Key", command=lambda: self.show_api_key(api_key_entry))
        show_api_key_btn.pack()
    
    def show_api_key(self, api_key_entry):
        api_key_entry.config(show="")
    
    def show_about(self):
        messagebox.showinfo("About", "Version 1.0\nThis is a description of the script.")
    
    def open_help(self):
        # Replace the URL with your desired help URL
        help_url = "https://example.com/help"
        messagebox.showinfo("Help", f"Visit {help_url} for assistance.")

# Create the main window
root = tk.Tk()

# Create the GUI object
gui = MyGUI(root)

# Start the main event loop
root.mainloop()
