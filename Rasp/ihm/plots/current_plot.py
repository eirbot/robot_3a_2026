import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

class CurrentPlotWindow:
    def __init__(self, parent, ina):
        self.ina = ina
        self.root = tk.Toplevel(parent)
        self.root.title("Évolution du courant (10 min)")
        self.root.geometry("800x400")

        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Temps (s)")
        self.ax.set_ylabel("Courant (A)")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._update_plot()

    def _update_plot(self):
        data = list(self.ina.history)
        if len(data) > 1:
            t0 = data[0][0]
            xs = [d[0] - t0 for d in data]
            ys = [d[1] for d in data]
            self.ax.clear()
            self.ax.plot(xs, ys, color="tabblue")
            self.ax.set_xlabel("Temps (s)")
            self.ax.set_ylabel("Courant (A)")
            self.ax.set_title("Historique 10 min")
            self.ax.grid(True)
        self.canvas.draw()
        self.root.after(1000, self._update_plot)
