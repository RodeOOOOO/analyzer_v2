import tkinter as tk
from tkinter import ttk
from processGUI import ProcessGUI


class InputWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("VNA Sweep Configuration")

        self.concentration_var = tk.StringVar()
        self.chemical_var = tk.StringVar()

        tk.Label(root, text="Enter Concentration (ppm):").grid(row=0, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.concentration_var).grid(row=0, column=1, padx=10, pady=10)

        tk.Label(root, text="Select Chemical:").grid(row=1, column=0, padx=10, pady=10)
        chemicals = ["PFOA", "PFOS", "PFBS", "PFNA"]
        self.chemical_dropdown = ttk.Combobox(root, textvariable=self.chemical_var, values=chemicals)
        self.chemical_dropdown.grid(row=1, column=1, padx=10, pady=10)
        self.chemical_dropdown.current(0)

        submit_button = tk.Button(root, text="Start Sweep", command=self.on_submit)
        submit_button.grid(row=2, column=0, columnspan=2, pady=20)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_submit(self):
        """Handle the submit button click, capture inputs, and start the process."""
        concentration = self.concentration_var.get()
        chemical = self.chemical_var.get()

        if concentration and chemical:
            self.root.destroy()
            self.start_process(concentration, chemical)

    def start_process(self, concentration, chemical):
        """Start the process sequence with the user inputs."""
        root = tk.Tk()
        process_gui = ProcessGUI(root, concentration, chemical)
        root.mainloop()

        return process_gui

    def on_close(self):
        """Handle window close event."""
        self.root.quit()
        self.root.destroy()


def show_input_window():
    root = tk.Tk()
    input_gui = InputWindow(root)
    root.mainloop()
