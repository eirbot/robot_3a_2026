

class Point:
    """Une classe représentant un point 2D."""

    def __init__(self, canvas, x=0, y=0, r=6):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.r = r
        self.id = canvas.create_oval(x*900/3-r+450, y*600/2-r, x*900/3+r+450, y*600/2+r, fill="blue", outline="")

    def move(self, dx, dy):
        self.canvas.move(self.id, dx, dy)
        self.x += dx/900*3
        self.y += dy/600*2

    def __repr__(self):
        """Représentation lisible dans la console."""
        return f"Point(x={self.x}, y={self.y})"
