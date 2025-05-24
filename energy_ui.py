import tkinter as tk

class EnergyUI:
    def __init__(self, root, initial_energy=100,
                 tired_callback=None, faint_callback=None, recover_callback=None,
                 sleep_start_callback=None, sleep_stop_callback=None):
        self.energy = initial_energy
        self.root = root

        self.tired_callback = tired_callback
        self.faint_callback = faint_callback
        self.recover_callback = recover_callback

        self.sleep_start_callback = sleep_start_callback
        self.sleep_stop_callback = sleep_stop_callback

        self.is_sleeping = False
        self.previous_state = "normal"

        # ====== Frame UI Energi ======
        self.frame = tk.Frame(root, bg="black", width=70, height=30)
        self.frame.place(x=10, y=5)

        # Label Energy
        self.label = tk.Label(
            self.frame,
            text="Energy",
            fg="white",
            bg="black",
            font=("Arial", 10, "bold")
        )
        self.label.place(x=0, y=0)

        # Canvas Bar Energi
        self.canvas = tk.Canvas(
            self.frame,
            width=80,
            height=15,
            bg="gray20",
            highlightthickness=0
        )
        self.canvas.place(x=0, y=20)
        self.bar = self.canvas.create_rectangle(0, 0, 60, 15, fill="#32F10B", width=0)

         # Pindah tombol ke root (bukan di dalam frame)
        self.sleep_button = tk.Button(
            root,  # ganti dari self.frame
            text="🌜Sleep",
            command=self.toggle_sleep,
            bg="#66e8ff",
            fg="#000000",
            font=("Arial", 10, "bold"),
            relief="flat",
            bd=1,
            activebackground="#0badec",
            activeforeground="#000000",
            cursor="hand2"
        )

        # Tempatkan di pojok kanan atas (misal: 5px dari kanan dan atas)
        self.sleep_button.place(relx=1.0, x=-40, y=5, width=50, height=20, anchor="ne")
        # Pastikan dalam frame

        self.update_bar()
        self.start_energy_loop()

    def toggle_sleep(self):
        self.is_sleeping = not self.is_sleeping
        if self.is_sleeping:
            self.sleep_button.config(text="☀️", bg="#f7de02", fg="#003366")
            if self.sleep_start_callback:
                self.sleep_start_callback()
        else:
            self.sleep_button.config(text="🌜Sleep", bg="#41a8b6", fg="#000000")
            if self.sleep_stop_callback:
                self.sleep_stop_callback()

    def update_bar(self):
        width = int(self.energy * 0.8)  # Skala ke 80px lebar
        self.canvas.coords(self.bar, 0, 0, width, 15)
        self.canvas.itemconfig(self.bar, fill=self.get_color())
        self.check_energy_state()

    def get_color(self):
        if self.energy > 66:
            return "#32FC0A"
        elif self.energy > 33:
            return "gold"
        else:
            return "red"

    def increase(self, amount):
        self.energy = min(self.energy + amount, 100)
        self.update_bar()

    def decrease(self, amount):
        self.energy = max(self.energy - amount, 0)
        self.update_bar()

    def get_energy(self):
        return self.energy

    def start_energy_loop(self):
        if self.is_sleeping:
            self.increase(0.2)
        else:
            self.decrease(1)
        self.root.after(3000, self.start_energy_loop)

    def check_energy_state(self):
        if self.energy == 0:
            if self.previous_state != "fainted":
                self.previous_state = "fainted"
                if self.faint_callback:
                    self.faint_callback()
        elif self.energy <= 20:
            if self.previous_state != "tired":
                self.previous_state = "tired"
                if self.tired_callback:
                    self.tired_callback()
        elif self.energy > 20:
            if self.previous_state in ["tired", "fainted"]:
                self.previous_state = "normal"
                if self.recover_callback:
                    self.recover_callback()

    def get_status(self):
        if self.energy == 0:
            return "fainted"
        elif self.energy <= 20:
            return "tired"
        else:
            return "normal"
