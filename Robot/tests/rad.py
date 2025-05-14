import math
import matplotlib.pyplot as plt

# Start- und Endpunkt
start = (300, 0)
end = (200, 200)

# Anzahl der Punkte
num_points = 20

# Funktion zur Berechnung des Radius (Abstand vom Ursprung)
def radius(p):
    return math.sqrt(p[0]**2 + p[1]**2)

# Berechne Radius am Start und Ende
r_start = radius(start)
r_end = radius(end)

# Erzeuge gleichmäßige Radien zwischen Start und Ende
radii = [r_start + i * (r_end - r_start) / (num_points - 1) for i in range(num_points)]

# Richtung vom Start zum Endpunkt
dir_x = end[0] - start[0]
dir_y = end[1] - start[1]

# Funktion zur Interpolation entlang der Linie basierend auf Radius
def find_point_with_radius(r_target, iterations=20):
    low = 0.0
    high = 1.0
    for _ in range(iterations):
        mid = (low + high) / 2
        x = start[0] + mid * dir_x
        y = start[1] + mid * dir_y
        r = radius((x, y))
        if r < r_target:
            low = mid
        else:
            high = mid
    x = start[0] + mid * dir_x
    y = start[1] + mid * dir_y
    return (x, y)

# Finde alle Punkte
points = [find_point_with_radius(r) for r in radii]

# Plotten (optional, matplotlib erforderlich)
x_vals = [p[0] for p in points]
y_vals = [p[1] for p in points]

plt.plot([start[0], end[0]], [start[1], end[1]], 'k--', label='Linie')
plt.plot(x_vals, y_vals, 'ro-', label='Punkte nach Radius')
plt.scatter(0, 0, color='blue', label='Ursprung (0,0)')
plt.legend()
plt.axis('equal')
plt.title("Punkte mit gleichmäßigem Radius-Abstand von (0,0)")
plt.show()
