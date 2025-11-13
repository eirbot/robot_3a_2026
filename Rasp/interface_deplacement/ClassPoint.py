

class Point:
    """Une classe représentant un point 2D."""

    def __init__(self, canvas, x=0, y=0, r=6):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.r = r
        self.id = canvas.create_oval(x*900/3-r+450, y*600/2-r, x*900/3+r+450, y*600/2+r, fill="blue", outline="")

    def moved(self, dx, dy):
        self.canvas.move(self.id, dx*900/3, dy*600/2)
        self.x += dx
        self.y += dy
        
    def move(self, x, y):
        self.canvas.coords(self.id, x*900/3-self.r+450, y*600/2-self.r, x*900/3+self.r+450, y*600/2+self.r)
        self.x = x
        self.y = y

    def __repr__(self):
        """Représentation lisible dans la console."""
        return f"Point(x={self.x}, y={self.y})"
