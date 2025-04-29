import serial
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Configura el puerto serial (ajusta el puerto según tu configuración)
ser = serial.Serial('COM4', 9600)

# Inicializa las listas para almacenar los datos
x_data = []

# Configura la figura y los ejes
plt.ion()
fig, ax = plt.subplots()
ax.set_xlabel('Muestras')
ax.set_ylabel('Valor del Acelerómetro (Eje X)')
line = Line2D([], [], label='X', color='b')
ax.add_line(line)
ax.legend(['X'])

try:
    while True:
        # Lee y decodifica los datos desde el puerto serial
        line_data = ser.readline().decode('utf-8').strip()

        # Divide los valores X, Y y Z
        values = line_data.split(',')
        if len(values) == 3:
            x, _, _ = map(int, values)

            # Añade los datos a las listas
            x_data.append(x)

            # Actualiza el plot en tiempo real
            line.set_xdata(range(len(x_data)))
            line.set_ydata(x_data)
            ax.relim()
            ax.autoscale_view()
            plt.pause(0.01)

except KeyboardInterrupt:
    ser.close()
    print("Serial closed.")
