"""
Kunda Archive GUI - Tkinter version (no dependencies needed!)
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path

# Import our Kunda compression library
sys.path.insert(0, os.path.dirname(__file__))
from kunda_ultra import KundaUltra


class KundaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kunda Archive - Ultra-Efficient Compression")
        self.root.geometry("900x700")
        
        # Variables
        self.selected_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.preset = tk.StringVar(value="ultra-128")
        self.include_checksum = tk.BooleanVar(value=True)
        
        # State
        self.is_compressing = False
        self.is_extracting = False
        self.compression_stats = {}
        
        # Setup UI
        self.setup_ui()
        
        # Apply modern theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply a modern dark theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        bg_color = '#2b2b2b'
        fg_color = '#ffffff'
        accent_color = '#3399ff'
        button_bg = '#404040'
        
        self.root.configure(bg=bg_color)
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=button_bg, foreground=fg_color)
        style.configure('Accent.TButton', background=accent_color, foreground=fg_color)
        style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
        style.configure('TNotebook', background=bg_color)
        style.configure('TNotebook.Tab', background=button_bg, foreground=fg_color)
        
    def setup_ui(self):
        """Setup the user interface."""
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="KUNDA ARCHIVE", 
                                font=('Arial', 16, 'bold'), foreground='#3399ff')
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text=" - Ultra-Efficient Compression",
                                   font=('Arial', 12))
        subtitle_label.pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=10)
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.compress_tab = ttk.Frame(self.notebook)
        self.extract_tab = ttk.Frame(self.notebook)
        self.about_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.compress_tab, text="📦 Compress")
        self.notebook.add(self.extract_tab, text="📂 Extract")
        self.notebook.add(self.about_tab, text="ℹ️ About")
        
        # Setup each tab
        self.setup_compress_tab()
        self.setup_extract_tab()
        self.setup_about_tab()
        
        # Log section
        self.setup_log_section()
    
    def setup_compress_tab(self):
        """Setup compression tab."""
        frame = ttk.Frame(self.compress_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Input folder
        ttk.Label(frame, text="Select folder to compress:", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, sticky=tk.EW, pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(input_frame, textvariable=self.selected_path).grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        ttk.Button(input_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=1)
        
        # Output file
        ttk.Label(frame, text="Output archive (.kun):", 
                 font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        output_frame = ttk.Frame(frame)
        output_frame.grid(row=3, column=0, sticky=tk.EW, pady=5)
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_path).grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        ttk.Button(output_frame, text="Save As...", command=self.browse_save).grid(row=0, column=1)
        
        # Settings
        ttk.Label(frame, text="Compression Settings:", 
                 font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(15, 5))
        
        settings_frame = ttk.Frame(frame)
        settings_frame.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(settings_frame, text="Preset:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        presets = ["fast", "balanced", "max", "ultra", "ultra-128", "ultra-256", "ultra-512"]
        preset_combo = ttk.Combobox(settings_frame, textvariable=self.preset, 
                                    values=presets, state='readonly', width=20)
        preset_combo.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Checkbutton(settings_frame, text="Include SHA256 checksum (+32 bytes)",
                       variable=self.include_checksum).grid(row=1, column=0, columnspan=2, 
                                                            sticky=tk.W, pady=(10, 0))
        
        # Compress button
        self.compress_btn = ttk.Button(frame, text="📦 Compress", 
                                       command=self.start_compression,
                                       style='Accent.TButton')
        self.compress_btn.grid(row=6, column=0, pady=20, sticky=tk.W)
        
        # Progress label
        self.compress_progress = ttk.Label(frame, text="", font=('Arial', 10))
        self.compress_progress.grid(row=7, column=0, sticky=tk.W)
        
        # Stats frame
        self.stats_frame = ttk.LabelFrame(frame, text="Compression Results", padding=10)
        self.stats_frame.grid(row=8, column=0, sticky=tk.EW, pady=10)
        self.stats_label = ttk.Label(self.stats_frame, text="", justify=tk.LEFT)
        self.stats_label.pack(anchor=tk.W)
        
        frame.columnconfigure(0, weight=1)
    
    def setup_extract_tab(self):
        """Setup extraction tab."""
        frame = ttk.Frame(self.extract_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Input archive
        ttk.Label(frame, text="Select .kun archive:", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, sticky=tk.EW, pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(input_frame, textvariable=self.selected_path).grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        ttk.Button(input_frame, text="Browse...", command=self.browse_archive).grid(row=0, column=1)
        
        # Output folder
        ttk.Label(frame, text="Extract to folder:", 
                 font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        output_frame = ttk.Frame(frame)
        output_frame.grid(row=3, column=0, sticky=tk.EW, pady=5)
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_path).grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self.browse_extract_folder).grid(row=0, column=1)
        
        # Extract button
        self.extract_btn = ttk.Button(frame, text="📂 Extract", 
                                      command=self.start_extraction,
                                      style='Accent.TButton')
        self.extract_btn.grid(row=4, column=0, pady=20, sticky=tk.W)
        
        # Progress label
        self.extract_progress = ttk.Label(frame, text="", font=('Arial', 10))
        self.extract_progress.grid(row=5, column=0, sticky=tk.W)
        
        frame.columnconfigure(0, weight=1)
    
    def setup_about_tab(self):
        """Setup about tab."""
        frame = ttk.Frame(self.about_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Kunda Archive Format", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        about_text = """A custom ultra-efficient archive format with minimal overhead 
(19-51 bytes), file deduplication, and powerful LZMA compression.

Features:
• Magic: KUNDA
• Extension: .kun
• Overhead: 19-51 bytes
• Compression: LZMA2/XZ
• File deduplication
• Path compression
• Optional SHA256 checksums

Made with Kunda magic ✨"""
        
        ttk.Label(frame, text=about_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def setup_log_section(self):
        """Setup log section at the bottom."""
        log_frame = ttk.LabelFrame(self.root, text="📝 Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10), ipady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD,
                                                   bg='#1e1e1e', fg='#ffffff',
                                                   font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored text
        self.log_text.tag_config('success', foreground='#4CAF50')
        self.log_text.tag_config('error', foreground='#f44336')
        self.log_text.tag_config('info', foreground='#2196F3')
    
    def log(self, message, level='info'):
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, full_message, level)
        self.log_text.see(tk.END)
        print(message)
    
    def browse_folder(self):
        """Browse for input folder."""
        folder = filedialog.askdirectory(title="Select folder to compress")
        if folder:
            self.selected_path.set(folder)
    
    def browse_save(self):
        """Browse for output file."""
        file = filedialog.asksaveasfilename(
            title="Save archive as",
            defaultextension=".kun",
            filetypes=[("Kunda Archive", "*.kun"), ("All Files", "*.*")]
        )
        if file:
            self.output_path.set(file)
    
    def browse_archive(self):
        """Browse for archive file."""
        file = filedialog.askopenfilename(
            title="Select Kunda archive",
            filetypes=[("Kunda Archive", "*.kun"), ("All Files", "*.*")]
        )
        if file:
            self.selected_path.set(file)
    
    def browse_extract_folder(self):
        """Browse for extraction folder."""
        folder = filedialog.askdirectory(title="Select extraction folder")
        if folder:
            self.output_path.set(folder)
    
    def start_compression(self):
        """Start compression in background thread."""
        if self.is_compressing or self.is_extracting:
            return
        
        if not self.selected_path.get() or not os.path.exists(self.selected_path.get()):
            self.log("✗ Please select a valid folder", 'error')
            return
        
        self.is_compressing = True
        self.compress_btn.config(state='disabled', text="⏳ Compressing...")
        self.compress_progress.config(text="Starting compression...", foreground='#2196F3')
        self.compression_stats = {}
        self.stats_label.config(text="")
        
        thread = threading.Thread(target=self.compress_thread)
        thread.daemon = True
        thread.start()
    
    def compress_thread(self):
        """Run compression in background."""
        try:
            self.log("Starting compression...", 'info')
            
            # Create output filename if not specified
            output = self.output_path.get()
            if not output:
                base_name = os.path.basename(self.selected_path.get().rstrip('/\\'))
                output = os.path.join(
                    os.path.dirname(self.selected_path.get()) or '.',
                    f"{base_name}.kun"
                )
                self.output_path.set(output)
            
            # Compress
            import io
            from contextlib import redirect_stdout
            
            captured = io.StringIO()
            with redirect_stdout(captured):
                KundaUltra.create(
                    self.selected_path.get(),
                    output,
                    self.preset.get(),
                    self.include_checksum.get()
                )
            
            # Parse output
            output_lines = captured.getvalue()
            for line in output_lines.split('\n'):
                if line.strip():
                    if '✓' in line:
                        self.log(line.strip(), 'success')
                    elif '✗' in line or 'Error' in line:
                        self.log(line.strip(), 'error')
                    else:
                        self.log(line.strip(), 'info')
                    
                    # Extract stats
                    if "Archive size:" in line:
                        self.compression_stats['Archive Size'] = line.split(':')[1].strip()
                    elif "Compression ratio:" in line:
                        self.compression_stats['Compression Ratio'] = line.split(':')[1].strip()
                    elif "Total time:" in line:
                        self.compression_stats['Total Time'] = line.split(':')[1].strip()
            
            # Update UI
            self.root.after(0, self.compression_complete, True)
            
        except Exception as e:
            self.log(f"✗ Error: {str(e)}", 'error')
            self.root.after(0, self.compression_complete, False)
    
    def compression_complete(self, success):
        """Called when compression completes."""
        self.is_compressing = False
        self.compress_btn.config(state='normal', text="📦 Compress")
        
        if success:
            self.compress_progress.config(text="✓ Compression successful!", foreground='#4CAF50')
            
            # Display stats
            if self.compression_stats:
                stats_text = "\n".join([f"{k}: {v}" for k, v in self.compression_stats.items()])
                self.stats_label.config(text=stats_text)
        else:
            self.compress_progress.config(text="✗ Compression failed", foreground='#f44336')
    
    def start_extraction(self):
        """Start extraction in background thread."""
        if self.is_compressing or self.is_extracting:
            return
        
        if not self.selected_path.get() or not os.path.exists(self.selected_path.get()):
            self.log("✗ Please select a valid .kun archive", 'error')
            return
        
        self.is_extracting = True
        self.extract_btn.config(state='disabled', text="⏳ Extracting...")
        self.extract_progress.config(text="Starting extraction...", foreground='#2196F3')
        
        thread = threading.Thread(target=self.extract_thread)
        thread.daemon = True
        thread.start()
    
    def extract_thread(self):
        """Run extraction in background."""
        try:
            self.log("Starting extraction...", 'info')
            
            # Create output folder if not specified
            output = self.output_path.get()
            if not output:
                base_name = os.path.splitext(os.path.basename(self.selected_path.get()))[0]
                output = os.path.join(
                    os.path.dirname(self.selected_path.get()) or '.',
                    f"{base_name}_extracted"
                )
                self.output_path.set(output)
            
            # Extract
            import io
            from contextlib import redirect_stdout
            
            captured = io.StringIO()
            with redirect_stdout(captured):
                KundaUltra.extract(self.selected_path.get(), output)
            
            # Log output
            for line in captured.getvalue().split('\n'):
                if line.strip():
                    if '✓' in line:
                        self.log(line.strip(), 'success')
                    elif '✗' in line or 'Error' in line:
                        self.log(line.strip(), 'error')
                    else:
                        self.log(line.strip(), 'info')
            
            self.root.after(0, self.extraction_complete, True)
            
        except Exception as e:
            self.log(f"✗ Error: {str(e)}", 'error')
            self.root.after(0, self.extraction_complete, False)
    
    def extraction_complete(self, success):
        """Called when extraction completes."""
        self.is_extracting = False
        self.extract_btn.config(state='normal', text="📂 Extract")
        
        if success:
            self.extract_progress.config(text="✓ Extraction successful!", foreground='#4CAF50')
        else:
            self.extract_progress.config(text="✗ Extraction failed", foreground='#f44336')


def main():
    """Run the application."""
    root = tk.Tk()
    app = KundaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()