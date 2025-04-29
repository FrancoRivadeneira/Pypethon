import urllib.request


import sys
import os
import glob
import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import urllib.request

import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtCore import QPropertyAnimation
from PyQt5.uic import loadUi
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
import time
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtGui import QImage, QPixmap
import pygame
from pygame.locals import *

import threading

import pygame
from PyQt5.QtCore import QThread, pyqtSignal
from pygame.locals import *
import tkinter as tk
from tkinter import filedialog
from PIL import ImageOps
from PIL import Image
import os
import csv
from ultralytics import YOLO
import cv2
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import serial


pygame.init()
pygame.joystick.init()

from datetime import datetime


data = '0.00'


#Declaramos Variables Locales
is_taking_pictures = False #determina si empezo el proceso de captura de imagenes
picture_directory = None #guarda la direccion mas reciente en la que se grabaron imagenes
picture_timer = None #guarda el temporizador para la captura de imagenes
ini = True #Bandera que indica cuando se empieze a grabar

forward = 0 #variable que indica si se esta avanzando, retorcediendo o si e robot esta detenido
forward_p = 0
d_prev = 0 #Guarda la anterior direccion del robot

distancia_abs = 0
encoder = 0
f_d = 3
reiniciar_flag = False
primera_vez = True

slider_pos = 0 #guarda la posicion del slider que indica la posicion
counter = 0 #COntador para la pantalla de carga
width = 960 #Ancho del video mostrado en la interfaz

height = 540 #Alto del video mostrado en la interfaz

fn = 'None' #Nombre del archivo anteriormente seleccionado
nega_fn = 'None' #Nombre del archivo procesado anteriormente seleccionado
current_index = 0 #Indice de la figura seleccionada dentro del folder correspondiente

flag_original = True #Bandera que indica si un set de imagenes ha sido seleccionado como original o como procesado

angv = 0 #Variable que guarda el angulo vertical de la camara
angh = 0 #Variable que guarda el angulo horizontal de la camara

i_pos = 0 #Variable de posicion que es transmitida desde el IMU. 
i_vel = 0 #Variable de velocidad que es transmitida desde el IMU. 

posicion_label = '0.0'
fallas=0


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(bytes)

    data_received = pyqtSignal(str)

    global ini
    global distancia_abs

    #Se inicia la clase Video Threat
    def __init__(self,directory):
        super().__init__()
        self.is_running = True
        self.directory = directory


    def run(self):
        global width
        global height
        global posicion_label
        global distancia_abs

        # Se define la camara que se desea utilizar
        cap = cv2.VideoCapture(0)

        # Se determina el tamanio de captura de imagen definido por las variables locales
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        counter = 1

        #Se inicia el primer threat
        while self.is_running:

            # Capture a frame
            ret, frame = cap.read()

            if ret:
                # En caso se halla cambiado el tama;o de senal del video por agrandar o encoger la pantalla se cambia el tamano de imagen. 
                if width != 960 or height != 540:
                    frame = cv2.resize(frame, (width, height))

                # Convertimos imagen a jpg
                is_success, buffer = cv2.imencode(".jpg", frame)
                if is_success:
                    # Emit the bytes signal
                    self.change_pixmap_signal.emit(buffer.tobytes())

            
                if is_taking_pictures:
                    #Se determina el tamano en el que se guardaran las imagenes.
                    frame = cv2.resize(frame, (1920, 1080))
                    
                    posicion_label = round(encoder,2)

                    posicion_label = str(posicion_label)

                    posicion_coma = posicion_label.replace('.', ',')
                    
                    tiempo = str(datetime.now().time())

                    tiempo = tiempo.replace('.',',')

                    tiempo = tiempo.replace(':',',')

                    file_name = f"{self.directory}/picture_{tiempo}_{posicion_coma}_cm_0_fallas.jpg" #CON TIEMPO

                    #file_name = f"{self.directory}/picture_{str(counter)}_{posicion_coma}_cm_0_fallas.jpg" #SIN TIEMPO

                    cv2.imwrite(file_name, frame)

                    counter += 1

                    print(f"Saved picture to {file_name}")               
        
        cap.release()


    def stop(self):
        self.is_running = False

class ControlThread(QThread):


    #Se declara el evento para conectar joysticks
    joystick_moved = pyqtSignal(float,int)

    #Se declara evento para conectar botones
    joystick_pressed = pyqtSignal(int)

    data_received = pyqtSignal(str)


    #Se inicia la clase Control. Esta esta en cargada del threat conectado al mando de PS4
    def __init__(self):
        super().__init__()

        pygame.init()
        pygame.joystick.init()
        



    def run(self):

        #llamamos las variables globales que albergan la direccion y la direccion anterior. 
        global forward
        global distancia_abs
        global d_prev
        global posicion_label
        global reiniciar_flag
        global primera_vez
        global f_d
        global encoder
        puerto_serie = serial.Serial('COM8', 9600)
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()


        #Se inicia el segundo threat
        while self.isRunning:
            ejecutando = True
            while ejecutando:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        ejecutando = False

                # Verificación si el botón 0 está presionado
                if self.controller.get_button(2):
                    dato='A'
                    print("adelante")
                    puerto_serie.write(dato.encode())
                elif self.controller.get_button(1):
                    dato='B'
                    print("atras")
                    puerto_serie.write(dato.encode())
                elif self.controller.get_button(4):
                    dato='C'
                    print("ddddddd")
                    puerto_serie.write(dato.encode())

                # Lógica del juego podría ir aquí

                # Control de la velocidad del bucle
                pygame.time.delay(150)

    # Lógica del juego podría ir aquí

    # Control de la velocidad del bucle
    

                


                

    def stop(self):
        self.running = False

#Menu Principal
class MainPage (QtWidgets.QMainWindow):

    def __init__(self):


        super(MainPage, self).__init__()

        #Cargamos interfaz principal
        loadUi ("src/GUI/interface.ui", self)


        #Quitamos el borde y adicionamos fondo transparente
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.reiniciar_encoder

        #Iniciamos la libreria para el joystick
        pygame.init()
        pygame.joystick.init()

        #Obtenemos numero que denota si el joystick esta conectado o no. 
        joystick_count = pygame.joystick.get_count()

        #Condicion en caso el joystick este conectado
        if joystick_count != 0:

            global distancia_abs

            #Iniciamos la clase correspondiente al control
            self.controller_thread = ControlThread()
            self.controller_thread.joystick_moved.connect(self.update_slider) #Funcion que constantemente cambiara el valor del slider correspondiente a la velocidad

            self.controller_thread.joystick_pressed.connect(self.update_slider_btn) #Funcion que constantemente cambia el texto que indica la direccion de avance del robot

            self.controller_thread.data_received.connect(self.receive)



            #Texto que indica la conexion del control
            self.controller_thread.start()
            self.label_18.setStyleSheet(f"color: #006400")
            self.label_18.setText('Conectado')
            font4 = QFont()
            font4.setPointSize(48)
            self.label_3.setFont(font4)


        #Condicion en caso el Joystick este desconectado
        else :
                #Texto que indica la conexion del control
                self.label_18.setStyleSheet(f"color: #FF0000")
                self.label_18.setText('Desconectado')
                font4 = QFont()
                font4.setPointSize(48)
                self.label_3.setFont(font4)
        
        self.video_thread = VideoThread(self)


#############################################################################################################################################
# BOTONES PARA REINICIAR ENCODER



        self.btn_exit.clicked.connect(self.reiniciar_encoder)

        self.close_window_button.clicked.connect(self.reiniciar_encoder)

        


#############################################################################################################################################
# BOTONES PARA ABRIR / CERRAR VENTANA

        #Minimize Window
        self.minimize_window_button.clicked.connect(lambda: self.showMinimized())
        self.minimize_window_button.enterEvent = self.minimize_window_button_enter_event #Cambio Color del boton
        self.minimize_window_button.leaveEvent = self.minimize_window_button_leave_event #Cambio Color del boton

        #Close window
        self.close_window_button.clicked.connect(lambda: self.close())
        self.close_window_button.enterEvent = self.close_window_button_enter_event #Cambio Color del boton
        self.close_window_button.leaveEvent = self.close_window_button_leave_event #Cambio Color del boton

        #Close Window Alternativa
        self.btn_exit.clicked.connect(lambda: self.close())
        self.btn_exit.enterEvent = self.btn_exit_enter_event #Cambio Color del boton
        self.btn_exit.leaveEvent = self.btn_exit_leave_event #Cambio Color del boton

        #Expand / Restore Window
        self.max_button.clicked.connect(lambda: self.showFullScreen())
        self.max_button.enterEvent = self.max_button_enter_event #Cambio Color del boton
        self.max_button.leaveEvent = self.max_button_leave_event #Cambio Color del boton

        #Funcion que aumenta tamano del video con el agrandamiento de pantalla
        self.max_button.clicked.connect(self.maximize_video)
        self.min_button.clicked.connect(self.minimize_video)

        #Achicar la interfaz
        self.min_button.clicked.connect(lambda: self.showNormal())
        self.min_button.enterEvent = self.min_button_enter_event #Cambio Color del boton
        self.min_button.leaveEvent = self.min_button_leave_event #Cambio Color del boton



        #Botones para el procesamiento de las imagenes deshabilitados
        self.btn_procesar.setEnabled(False)
        self.btn_original.setEnabled(False)
        self.btn_procesado.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_prev.setEnabled(False)


        #SLIDERS

        self.angulov_slider.valueChanged.connect(self.update_angulov) #Actualiza Slider Angulo Vertical Camara
        self.anguloh_slider.valueChanged.connect(self.update_anguloh) #Actualiza Slider Angulo Horizontal Camara
        self.velocidad_slider.valueChanged.connect(self.update_velocidad) #Actualiza Slider Velocidad Robot


        
        #BOTONES PARA GRABAR
        self.btn_grabar.clicked.connect(self.start_taking_pictures)
        self.btn_grabar.enterEvent = self.btn_grabar_enter_event #Cambiar Color boton
        self.btn_grabar.leaveEvent = self.btn_grabar_leave_event #Cambiar Color boton


        #BOTONES PARA PARAR DE GRABAR
        self.btn_stop.clicked.connect(self.stop_recording)
        self.btn_stop.enterEvent = self.btn_stop_enter_event #Cambiar Color boton
        self.btn_stop.leaveEvent = self.btn_stop_leave_event #Cambiar Color boton



        #BOTONES PARA ABRIR ARCHIVOS:
        self.btn_archivo.clicked.connect(self.open_file_dialog)
        self.btn_archivo.enterEvent = self.btn_archivo_enter_event #Cambiar Color boton
        self.btn_archivo.leaveEvent = self.btn_archivo_leave_event #Cambiar Color boton

        #BOTONES PARA PROCESAR LAS IMAGENES:
        self.btn_procesar.clicked.connect(self.process_file)
        self.btn_procesar.enterEvent = self.btn_procesar_enter_event #Cambiar Color boton
        self.btn_procesar.leaveEvent = self.btn_procesar_leave_event #Cambiar Color boton

        #BOTON PARA MOSTRAR IMAGNE ORIGINAL
        self.btn_original.clicked.connect(self.original_file)
        self.btn_original.enterEvent = self.btn_original_enter_event #Cambiar Color boton
        self.btn_original.leaveEvent = self.btn_original_leave_event #Cambiar Color boton

        #BOTON PARA MOSTRAR IMAGEN PROCESADA
        self.btn_procesado.clicked.connect(self.processed_file)
        self.btn_procesado.enterEvent = self.btn_procesado_enter_event #Cambiar Color boton
        self.btn_procesado.leaveEvent = self.btn_procesado_leave_event #Cambiar Color boton


        #Botones para probar preder y apagar los LEDs. 
        self.btn_angh.clicked.connect(self.led_on)
        self.btn_angv.clicked.connect(self.led_off)


        #INICIAMOS TIMER PARA MOSTRAR SECUENCIA DE IMAGENES
        self.timer = QTimer()


        #Iniciamos bandera que indica que la secuencia de imagenes no se esta mostrando
        self.is_playing = False


        #BOTON PARA INICAR SECUENCIA DE IMAGENES
        self.btn_play.clicked.connect(self.start_sequence)
        self.btn_play.enterEvent = self.btn_play_enter_event #Cambiar Color boton
        self.btn_play.leaveEvent = self.btn_play_leave_event #Cambiar Color boton

        #BOTON PARA PAUSAR SECUENCIA DE IMAGENES
        self.btn_pause.clicked.connect(self.pause_sequence)
        self.btn_pause.enterEvent = self.btn_pause_enter_event #Cambiar Color boton
        self.btn_pause.leaveEvent = self.btn_pause_leave_event #Cambiar Color boton

        #BOTON PARA SIGUIENTE IMAGEN SECUENCIA DE IMAGENES
        self.btn_next.clicked.connect(self.next_image)
        self.btn_next.enterEvent = self.btn_next_enter_event #Cambiar Color boton
        self.btn_next.leaveEvent = self.btn_next_leave_event #Cambiar Color boton

        #BOTON PARA ANTERIOR IMAGEN SECUENCIA DE IMAGENES
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_prev.enterEvent = self.btn_prev_enter_event #Cambiar Color boton
        self.btn_prev.leaveEvent = self.btn_prev_leave_event #Cambiar Color boton

        #Muestra la siguiente imagen segun el timer anteriormente inicializado. 
        self.timer.timeout.connect(self.show_next_image)
     


        #FUNCION QUE PERMITE ARRASTRAR LA VENTANA POR LA PANTALLA
        def moveWindow(e):
            # Primero verificamos si la ventana esta maximizada
            if self.isFullScreen() == False: #Not maximized
                #Solo movemos si la ventana no esta agrandada
                # ###############################################
                #Arrastramos la ventana cuando se hace click izquierdo con el mouse
                if e.buttons() == Qt.LeftButton:  
                    #Movemos ventana
                    self.move(self.pos() + e.globalPos() - self.clickPosition)
                    self.clickPosition = e.globalPos()
                    e.accept()
        #######################################################################




        #Mover ventana 
        self.header_frame.mouseMoveEvent = moveWindow
        self.open_close_side_bar_btn.clicked.connect(lambda: self.slideLeftMenu())
        self.open_close_side_bar_btn.enterEvent = self.open_close_side_bar_btn_enter_event
        self.open_close_side_bar_btn.leaveEvent = self.open_close_side_bar_btn_leave_event

###########################################################  BOTONOES PARA DISTRIBUIR LA PANTALAL PRINCIPAL AL DAR CLICK EN BOTONES DEL MENU ############################################################ 
        self.btn_camara.clicked.connect(self.distribuir_camara)
        self.btn_camara.enterEvent = self.btn_camara_enter_event
        self.btn_camara.leaveEvent = self.btn_camara_leave_event


        self.btn_angulo.clicked.connect(self.distribuir)
        self.btn_angulo.enterEvent = self.btn_angulo_enter_event
        self.btn_angulo.leaveEvent = self.btn_angulo_leave_event

        self.btn_control.clicked.connect(self.distribuir_control)
        self.btn_control.enterEvent = self.btn_control_enter_event
        self.btn_control.leaveEvent = self.btn_control_leave_event

        self.btn_archivos.clicked.connect(self.distribuir_archivos)
        self.btn_archivos.enterEvent = self.btn_archivos_enter_event
        self.btn_archivos.leaveEvent = self.btn_archivos_leave_event

        self.btn_posicion.clicked.connect(self.distribuir_posicion)
        self.btn_posicion.enterEvent = self.btn_posicion_enter_event
        self.btn_posicion.leaveEvent = self.btn_posicion_leave_event

        self.btn_reset.clicked.connect(self.reset_button)
        self.btn_reset.enterEvent = self.btn_reset_enter_event
        self.btn_reset.leaveEvent = self.btn_reset_leave_event

        

    def update_label(self, data):

        self.label_21.setText(data)

    # colro claro: rgb(27, 219, 159)
    # colro super claro: rgb(27, 250, 200) 
    # color oscuro rgb(6, 44, 44)



################################## CAMBIO DE COLOR E ICONOS DE BOTONES AL PASAR MOUSE SOBRE ELLOS ############################################################################

    # colro claro: rgb(27, 219, 159)
    # colro claro: rgb(27, 250, 200)
    # color oscuro rgb(6, 44, 44)

    def btn_camara_enter_event (self, event):
        # Change the button color when hovered
        self.btn_camara.setStyleSheet("QPushButton {border: none; background-color: rgb(44,190, 255);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_camara_leave_event (self, event):
        # Change the button color when hovered
        self.btn_camara.setStyleSheet("QPushButton {border: none; background-color: rgb(90,183, 194);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_angulo_enter_event (self, event):
        # Change the button color when hovered
        self.btn_angulo.setStyleSheet("QPushButton {border: none; background-color: rgb(44,190, 255);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_angulo_leave_event (self, event):
        # Change the button color when hovered
        self.btn_angulo.setStyleSheet("QPushButton {border: none; background-color: rgb(90,183, 194);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_control_enter_event (self, event):
        # Change the button color when hovered
        self.btn_control.setStyleSheet("QPushButton {border: none; background-color: rgb(44,190, 255);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_control_leave_event (self, event):
        # Change the button color when hovered
        self.btn_control.setStyleSheet("QPushButton {border: none; background-color: rgb(90,183, 194);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_archivos_enter_event (self, event):
        # Change the button color when hovered
        self.btn_archivos.setStyleSheet("QPushButton {border: none; background-color: rgb(44,190, 255);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_archivos_leave_event (self, event):
        # Change the button color when hovered
        self.btn_archivos.setStyleSheet("QPushButton {border: none; background-color: rgb(90,183, 194);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_posicion_enter_event (self, event):
        # Change the button color when hovered
        self.btn_posicion.setStyleSheet("QPushButton {border: none; background-color: rgb(44,190, 255);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_posicion_leave_event (self, event):
        # Change the button color when hovered
        self.btn_posicion.setStyleSheet("QPushButton {border: none; background-color: rgb(90,183, 194);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_play_enter_event (self, event):
        # Change the button color when hovered
        self.btn_play.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_play_leave_event (self, event):
        # Change the button color when hovered
        self.btn_play.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_pause_enter_event (self, event):
        # Change the button color when hovered
        self.btn_pause.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_pause_leave_event (self, event):
        # Change the button color when hovered
        self.btn_pause.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_next_enter_event (self, event):
        # Change the button color when hovered
        self.btn_next.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_next_leave_event (self, event):
        # Change the button color when hovered
        self.btn_next.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_prev_enter_event (self, event):
        # Change the button color when hovered
        self.btn_prev.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_prev_leave_event (self, event):
        # Change the button color when hovered
        self.btn_prev.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")




    def btn_grabar_enter_event (self, event):
        # Change the button color when hovered
        self.btn_grabar.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_grabar_leave_event (self, event):
        # Change the button color when hovered
        self.btn_grabar.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_stop_enter_event (self, event):
        # Change the button color when hovered
        self.btn_stop.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_stop_leave_event (self, event):
        # Change the button color when hovered
        self.btn_stop.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_archivo_enter_event (self, event):
        # Change the button color when hovered
        self.btn_archivo.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_archivo_leave_event (self, event):
        # Change the button color when hovered
        self.btn_archivo.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_procesar_enter_event (self, event):
        # Change the button color when hovered
        self.btn_procesar.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_procesar_leave_event (self, event):
        # Change the button color when hovered
        self.btn_procesar.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_original_enter_event (self, event):
        # Change the button color when hovered
        self.btn_original.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_original_leave_event (self, event):
        # Change the button color when hovered
        self.btn_original.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_procesado_enter_event (self, event):
        # Change the button color when hovered
        self.btn_procesado.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_procesado_leave_event (self, event):
        # Change the button color when hovered
        self.btn_procesado.setStyleSheet("QPushButton {border: none; background-color: rgb(6, 44, 44);border-radius: 10px; color: rgb(255, 255, 255) }")

    def btn_reset_enter_event (self, event):
        # Change the button color when hovered
        self.btn_reset.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_reset_leave_event (self, event):
        # Change the button color when hovered
        self.btn_reset.setStyleSheet("QPushButton {border: none; background-color: transparent; border-radius: 10px; color: rgb(255, 255, 255) }")


    def btn_exit_enter_event (self, event):
        # Change the button color when hovered
        self.btn_exit.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def btn_exit_leave_event (self, event):
        # Change the button color when hovered
        self.btn_exit.setStyleSheet("QPushButton {border: none; background-color: transparent;border-radius: 10px; color: rgb(255, 255, 255) }")

    def close_window_button_enter_event (self, event):
        # Change the button color when hovered
        self.close_window_button.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def close_window_button_leave_event (self, event):
        # Change the button color when hovered
        self.close_window_button.setStyleSheet("QPushButton {border: none; background-color: transparent;border-radius: 10px; color: rgb(255, 255, 255) }")

    def max_button_enter_event (self, event):
        # Change the button color when hovered
        self.max_button.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def max_button_leave_event (self, event):
        # Change the button color when hovered
        self.max_button.setStyleSheet("QPushButton {border: none; background-color: transparent;border-radius: 10px; color: rgb(255, 255, 255) }")


    def min_button_enter_event (self, event):
        # Change the button color when hovered
        self.min_button.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def min_button_leave_event (self, event):
        # Change the button color when hovered
        self.min_button.setStyleSheet("QPushButton {border: none; background-color: transparent;border-radius: 10px; color: rgb(255, 255, 255) }")


    def minimize_window_button_enter_event (self, event):
        # Change the button color when hovered
        self.minimize_window_button.setStyleSheet("QPushButton {border: none; background-color: rgb(27, 250, 200);border-radius: 10px; color: rgb(255, 255, 255) }")
    def minimize_window_button_leave_event (self, event):
        # Change the button color when hovered
        self.minimize_window_button.setStyleSheet("QPushButton {border: none; background-color: transparent;border-radius: 10px; color: rgb(255, 255, 255) }")




    def open_close_side_bar_btn_enter_event (self, event):

        width = self.slide_menu_container.width()
        if width <= 0:
            # Change the button color when hovered
            self.open_close_side_bar_btn.setIcon(QtGui.QIcon(u"Iconos/menu2.png"))

        else:
            # Change the button color when hovered
            self.open_close_side_bar_btn.setIcon(QtGui.QIcon(u"Iconos/left2.png"))


    def open_close_side_bar_btn_leave_event (self, event):

        width = self.slide_menu_container.width()
        if width <= 0:
            # Change the button color when hovered
            self.open_close_side_bar_btn.setIcon(QtGui.QIcon(u"Iconos/menu.png"))

        else:
            # Change the button color when hovered
            self.open_close_side_bar_btn.setIcon(QtGui.QIcon(u"Iconos/left.png"))

#########################################################################################################################################################################

#Funcion que reinicia el conteo del encoder cuando se cierre la interfaz. 
    def reiniciar_encoder(self):

        global reiniciar_flag

        reiniciar_flag  = True       
        
             
#########################################################################################################################################################################


# LED
        
    #FUNCION QUE ENCIENDE EL LED
    def led_on (self):

        global str_riva

        #try catch por si LED no esta conectado
        try:

            ser = serial.Serial('COM3', 9600)  
            ser.write(b'1')
            ser.close()

        except:
            ser = 'hola'


    #FUNCION QUE APAGA LED
    def led_off (self):
        global str_riva

        try:
            #try catch por si LED no esta conectado
            ser = serial.Serial('COM3', 9600)  
            ser.write(b'0')
            ser.close()

        except:
            ser = 'hola'


   

#########################################################################################################################################################################

#SECUENCIA PLAY Y PAUSA


    def start_sequence (self):
        # Open a file dialog windo
        global fn
        global nega_fn

        self.original_folder = os.path.dirname(fn)
        self.original_list = sorted(os.listdir(self.original_folder))


        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_procesar.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_prev.setEnabled(False)

        #De igual manera mostramos la posicion y la cantidad de fallas
        
        print ('Sequence Started')

        if not self.is_playing:
               self.is_playing = True
               #current_index = 0
               self.timer.start(100)  # show next image every 0.1 seconds

        else:
               self.timer.start(100)


        try:
            self.nega_folder = os.path.dirname(nega_fn)
            self.nega_list = sorted(os.listdir(self.nega_folder))

        except:

            print('Aun no se ha procesado algun archivo')


    def pause_sequence (self):

        global nega_fn
        global flag_original

        # Open a file dialog window
        self.timer.stop()
        print ('Sequence Stoped')

        self.btn_play.setEnabled(True)

        self.btn_pause.setEnabled(False)

        self.btn_next.setEnabled(True)
        self.btn_prev.setEnabled(True)

        
        if  not os.path.exists(os.path.dirname(nega_fn)):

            self.btn_procesar.setEnabled(True)

    def next_image (self):

        global current_index
        global fn
        global nega_fn

        if flag_original:

            current_index += 1
            if current_index > len(self.original_list)-1:
                current_index = 0
            image_path = os.path.join(self.original_folder, self.original_list[current_index])
            fn = image_path
            pixmap = QPixmap(image_path)
            print(str(current_index))
            self.label_24.setPixmap(pixmap)


            

            

        else:
            current_index += 1
            if current_index > len(self.nega_list)-1:
                current_index = 0
            image_path = os.path.join(self.nega_folder, self.nega_list[current_index])
            nega_fn = image_path
            pixmap = QPixmap(image_path)
            print(str(current_index))
            self.label_24.setPixmap(pixmap)
            

        name_1 = os.path.basename(image_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')
        p = words[2]
        f = words[4]

        self.label_20.setText(str(p) + ' cm')
        self.label_22.setText(f)
        

    def prev_image (self):

        global current_index
        global fn
        global nega_fn

        if flag_original:

            current_index -= 1
            if current_index < 0:
                current_index = len(self.original_list)-1

            image_path = os.path.join(self.original_folder, self.original_list[current_index])
            fn = image_path
            pixmap = QPixmap(image_path)
            print(str(current_index))

            self.label_24.setPixmap(pixmap)

        else:
            current_index -= 1

            if current_index < 0:
                current_index = len(self.nega_list)-1

            image_path = os.path.join(self.nega_folder, self.nega_list[current_index])
            nega_fn = image_path
            pixmap = QPixmap(image_path)
            print(str(current_index))
            self.label_24.setPixmap(pixmap)

        name_1 = os.path.basename(image_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')
        p = words[2]
        f = words[4]


        self.label_20.setText(str(p) + ' cm')
        self.label_22.setText(f)

    def show_next_image (self):
        # Open a file dialog window

        global current_index
        global fn
        global nega_fn


        if flag_original:

            
                
            current_index += 1

            if current_index > len(self.original_list)-1:
                current_index = 0
                if not self.is_playing:
                    return
                
            image_path = os.path.join(self.original_folder, self.original_list[current_index])
            fn = image_path
            pixmap = QPixmap(image_path)
            print(str(current_index))
            self.label_24.setPixmap(pixmap)


            
            

            

        else:

            current_index += 1
            if current_index > len(self.nega_list)-1:
                current_index = 0
                if not self.is_playing:
                    return
            
            image_path = os.path.join(self.nega_folder, self.nega_list[current_index])
            nega_fn = image_path
            pixmap = QPixmap(image_path)
            print(str(current_index))
            self.label_24.setPixmap(pixmap)
            

        name_1 = os.path.basename(image_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')
        p = words[2]
        f = words[4]

    
        self.label_20.setText(str(p) + ' cm')
        self.label_22.setText(f)
           


#########################################################################################################################################################################

# Funciones para abrir y procesar archivos

    def open_file_dialog(self):
        # Open a file dialog window


        global fn

        global nega_fn

        global current_index

        current_index = 0

        #Activamos botones
        self.btn_procesado.setEnabled(False)
        self.btn_original.setEnabled(False)
        self.btn_procesar.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(False)


        #Pedimos a usuario que seleccione el archivo deseaado
        filename, _ = QFileDialog.getOpenFileName(self, 'Open Image', '', 'Image files (*.png *.jpg *.jpeg)')


        file_extension = os.path.splitext(filename)[1]

        #Removemos el punto de la extension del archivo
        file_extension = file_extension[1:]

        #Solo confirmmamos si se ha seleccionado una imagen
        if (file_extension == 'jpg') or (file_extension == 'png'):

            self.btn_original.setEnabled(True)
            self.btn_procesar.setEnabled(True)
            self.btn_play.setEnabled(True)
            self.btn_pause.setEnabled(True)
            self.btn_next.setEnabled(True)
            self.btn_prev.setEnabled(True)


        #Guardamos ruta de archivo en la variable local
        fn = filename

        #A partir de la imagen seleccionada obtenemos el directorio de las imagenes.
        self.original_folder = os.path.dirname(fn)
        self.original_list = sorted(os.listdir(self.original_folder))

        #En caso se seleccione imagen procesada, se verifica si esta carpeta esta debidamente guardada
        nega_folder = os.path.dirname((os.path.dirname(fn))) + '/Nega'

        #Si existe y esa debidamente guardada, la mostramos.
        if os.path.exists(nega_folder):
            #Crea la carpeta de imagenes negativas

            file_extension = fn.replace('.jpg','')
            nega_fn =  nega_folder + '/' +  os.path.basename(file_extension) + '_nega.jpg'
            self.nega_folder = os.path.dirname(nega_fn)
            self.nega_list = sorted(os.listdir(self.nega_folder))

            if file_extension == 'jpg':

                self.btn_procesar.setEnabled(False)
                self.btn_procesado.setEnabled(True)
                self.btn_next.setEnabled(True)
                self.btn_prev.setEnabled(True)

        print (fn)


        # Entonces mostramos la imagen designada en la label correspondiente
        pixmap = QtGui.QPixmap(filename)
        self.label_24.setPixmap(pixmap)
        self.label_24.setScaledContents(True)

        #De igual manera mostramos la posicion y la cantidad de fallas
        name_1 = os.path.basename(filename)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')
        """
        p = words[2]
        f = words[4]


        self.label_20.setText(str(p) + ' cm')
        self.label_22.setText(f)"""

        #Seleccionamos el folder en el que se encuentra guardada la imagen
        folder_name = os.path.basename(os.path.dirname(filename))

        #Indicamos en un texto el folder al que pertenece
        self.label_23.setText(folder_name)


    def process_file(self):
        # Open a file dialog window

        global fn
        global nega_fn
        global flag_original
        global current_index
        global fallas

        flag_original = False

#################################### OBTENEMOS RUTAS NECESARIAS #####################################################################################################  
        
        fn_folder = os.path.dirname(fn) #Obtenemos la carpeta Original

        folder_name = os.path.basename(os.path.dirname(fn_folder)) #Obtenemos el nombre de la carpeta en la que se guardo la prueba
        
        files = os.listdir(fn_folder)

        image_files = [file for file in files if file.endswith('.jpg')]

        csv_file_path = os.path.dirname(fn_folder) + '/' + folder_name + '_Datos_Originales.csv' #Ubicacion para cvs original


#################################### GUARDAMOS CSV SIN PROCESAr  #####################################################################################################  

        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            # Write the header row
            writer.writerow(['Date', 'Time', 'Distance (cm)', 'No. of Holes', 'Fallas'])

            # Write each image information as a separate row
            for image_file in image_files:
                # Split the image name using the '_' character
                image_info = image_file.split('_')

                # Write each word as a separate column
                writer.writerow(image_info)

        
#################################### PROCESAMOS EL SET DE IMAGENES  #####################################################################################################  

        self.btn_procesado.setEnabled(True)

        self.btn_procesar.setEnabled(False)

        #Se crea la carpeta si no existe
        if not os.path.exists(os.path.dirname(fn_folder) + '/Process'):
            #Crea la carpeta de imagenes negativas
            os.makedirs(os.path.dirname(fn_folder) + '/Process')    

        
        
        #Guarda la carpeta negativa
        nega_folder = os.path.dirname(fn_folder) + '/Process'

        MODEL_PATH = os.path.join('.', 'runs', 'detect', 'train', 'weights', 'best.pt')

        # Load a model
        model = YOLO(MODEL_PATH)  # load a custom model

        image_pattern = os.path.join(fn_folder, '*.jpg')
        image_files = glob.glob(image_pattern)

        ni = len(image_files)
        i2 = 0

        self.label_23.setText('0/' + str(ni))


        for filename in os.listdir(fn_folder):

            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                # Open the image file
                image = cv2.imread(os.path.join(fn_folder, filename))

                inverted_img = image
                result_image = image.copy()

                # Perform object detection on the image
                results = model(image)
                annotated_frame=results[0].plot()

                counter = 0  # Counter for detected objects
                
                i2 += 1
                self.label_23.setText( str(i2) + '/' + str(ni))


                # Print the number of objects detected
                #print(f"Number of objects detected: {counter}")

                n_fn = filename.replace('0_fallas', str(counter) + '_fallas')
                n_fn =  n_fn.replace('.jpg', '')


                # Save the inverted image to the output folder with the same filename
                cv2.imwrite(nega_folder + '/' + n_fn + '_Segmentado.jpg',annotated_frame)



#################################### GUARDAMOS CSV YA PROCESADO  #####################################################################################################  

        csv_file_path = os.path.dirname(fn_folder) + '/' + folder_name + '_Datos_Procesados.csv' #Ubicacion para cvs procesado

        files = os.listdir(nega_folder)

        image_files = [file for file in files if file.endswith('.jpg')]

        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            
            # Write the header row
            writer.writerow(['Date', 'Time', 'Distance (cm)', 'No. of Holes', 'Fallas'])

            # Write each image information as a separate row
            for image_file in image_files:
                # Split the image name using the '_' character
                image_info = image_file.split('_')

                # Write each word as a separate column
                writer.writerow(image_info)

#################################### INDICAMOS MEDIANTE TEXTO QUE SE PROCESARON LAS IMAGENES  #####################################################################################################  

        #Seleccionamos el folder en el que se encuentra guardada la imagen
        folder_name = os.path.basename(os.path.dirname(fn))

        #Indicamos en un texto el folder al que pertenece
        self.label_23.setText('Archivo Procesado')

        fallas = counter


        #Guarda la ruta a la primera imagen negativa
        images_list = sorted(os.listdir(nega_folder))
        new_file_path = os.path.join(nega_folder , images_list[current_index])

        #Guardamos la variable global de la primera imagen
        nega_fn = new_file_path

        self.nega_folder = os.path.dirname(nega_fn)
        self.nega_list = sorted(os.listdir(self.nega_folder))


#################################### MOSTRAMOS LA PRIMERA IMAGEN PROCESADA EN LA PANTALLA  #####################################################################################################  

        pixmap = QtGui.QPixmap(new_file_path)
        self.label_24.setPixmap(pixmap)
        self.label_24.setScaledContents(True)

        name_1 = os.path.basename(new_file_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')

        #p = words[2]
        #f = words[4]


        #self.label_20.setText(str(p) + ' cm')
        #self.label_22.setText(f)


        #print(fn)

        #print(nega_fn)
########################################################################################################################################################################################################
    def process_class_file(self):
        # Open a file dialog window

        global fn
        global nega_fn
        global flag_original
        global current_index
        global fallas

        flag_original = False

#################################### OBTENEMOS RUTAS NECESARIAS #####################################################################################################  
        
        fn_folder = os.path.dirname(fn) #Obtenemos la carpeta Original

        folder_name = os.path.basename(os.path.dirname(fn_folder)) #Obtenemos el nombre de la carpeta en la que se guardo la prueba
        
        files = os.listdir(fn_folder)

        image_files = [file for file in files if file.endswith('.jpg')]

        csv_file_path = os.path.dirname(fn_folder) + '/' + folder_name + '_Datos_Originales.csv' #Ubicacion para cvs original


#################################### GUARDAMOS CSV SIN PROCESAr  #####################################################################################################  

        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            # Write the header row
            writer.writerow(['Date', 'Time', 'Distance (cm)', 'No. of Holes', 'Fallas'])

            # Write each image information as a separate row
            for image_file in image_files:
                # Split the image name using the '_' character
                image_info = image_file.split('_')

                # Write each word as a separate column
                writer.writerow(image_info)

        
#################################### PROCESAMOS EL SET DE IMAGENES  #####################################################################################################  

        self.btn_procesado.setEnabled(True)

        self.btn_procesar.setEnabled(False)

        #Se crea la carpeta si no existe
        if not os.path.exists(os.path.dirname(fn_folder) + '/Classification'):
            #Crea la carpeta de imagenes negativas
            os.makedirs(os.path.dirname(fn_folder) + '/Classification')    

        
        
        #Guarda la carpeta negativa
        class_folder = os.path.dirname(fn_folder) + '/Classification'


        # IMAGE_PATH = os.path.join('.', 'images', 'test', 'captured_image_4.jpg')
        MODEL_PATH = os.path.join('.', 'runs', 'detect', 'train', 'weights', 'best.pt')

        # Load a model
        model = YOLO(MODEL_PATH)  # load a custom model


        image_pattern = os.path.join(fn_folder, '*.jpg')
        image_files = glob.glob(image_pattern)

        ni = len(image_files)
        i2 = 0

        self.label_23.setText('0/' + str(ni))


        for filename in os.listdir(fn_folder):

            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                # Open the image file
                image = cv2.imread(os.path.join(fn_folder, filename))
                # Perform object detection on the image
                results = model(image)
                annotated_frame=results[0].plot()

                counter = 0  # Counter for detected objects
                i2 += 1
                self.label_23.setText( str(i2) + '/' + str(ni))

                n_fn = filename.replace('0_fallas', str(counter) + '_fallas')
                n_fn =  n_fn.replace('.jpg', '')


                # Save the inverted image to the output folder with the same filename
                cv2.imwrite(class_folder + '/' + n_fn + '_classification.jpg',annotated_frame)



#################################### GUARDAMOS CSV YA PROCESADO  #####################################################################################################  

        csv_file_path = os.path.dirname(fn_folder) + '/' + folder_name + '_Datos_Procesados.csv' #Ubicacion para cvs procesado

        files = os.listdir(class_folder)

        image_files = [file for file in files if file.endswith('.jpg')]

        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            
            # Write the header row
            writer.writerow(['Date', 'Time', 'Distance (cm)', 'No. of Holes', 'Fallas'])

            # Write each image information as a separate row
            for image_file in image_files:
                # Split the image name using the '_' character
                image_info = image_file.split('_')

                # Write each word as a separate column
                writer.writerow(image_info)

#################################### INDICAMOS MEDIANTE TEXTO QUE SE PROCESARON LAS IMAGENES  #####################################################################################################  

        #Seleccionamos el folder en el que se encuentra guardada la imagen
        folder_name = os.path.basename(os.path.dirname(fn))

        #Indicamos en un texto el folder al que pertenece
        self.label_23.setText('Archivo Procesado')

        fallas = counter


        #Guarda la ruta a la primera imagen negativa
        images_list = sorted(os.listdir(class_folder))
        new_file_path = os.path.join(class_folder , images_list[current_index])

        #Guardamos la variable global de la primera imagen
        nega_fn = new_file_path

        self.nega_folder = os.path.dirname(nega_fn)
        self.nega_list = sorted(os.listdir(self.nega_folder))


#################################### MOSTRAMOS LA PRIMERA IMAGEN PROCESADA EN LA PANTALLA  #####################################################################################################  

        pixmap = QtGui.QPixmap(new_file_path)
        self.label_24.setPixmap(pixmap)
        self.label_24.setScaledContents(True)

        name_1 = os.path.basename(new_file_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')

        #p = words[2]
        #f = words[4]


        #self.label_20.setText(str(p) + ' cm')
        #self.label_22.setText(f)


        #print(fn)

        #print(nega_fn)
########################################################################################################################################################################################################

    def original_file(self):
        # Open a file dialog window


        global fn
        global flag_original
        global current_index

        folder = os.path.dirname(os.path.dirname(fn)) + "/Original"

        images_list = sorted(os.listdir(folder))

        new_file_path = os.path.join(folder , images_list[current_index])

        flag_original = True


        self.label_23.setText('Archivo Original')

        # Display the selected image on the label
        pixmap = QtGui.QPixmap(new_file_path)
        self.label_24.setPixmap(pixmap)
        self.label_24.setScaledContents(True)

        name_1 = os.path.basename(new_file_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')

        p = words[2]
        f = words[4]


        self.label_20.setText(str(p) + ' cm')
        self.label_22.setText(f)
        

    def processed_file(self):
        # Open a file dialog window

        global flag_original
        global current_index

        flag_original = False

        global nega_fn


        folder = os.path.dirname(nega_fn)

        print (folder)

        images_list = sorted(os.listdir(folder))


        new_file_path = os.path.join(folder , images_list[current_index])

        flag_original = False

        self.label_23.setText('Archivo Procesado')
        # Display the selected image on the label
        pixmap = QtGui.QPixmap(new_file_path)
        self.label_24.setPixmap(pixmap)
        self.label_24.setScaledContents(True)

        name_1 = os.path.basename(new_file_path)  # Obtenemos el nomre de la imagen donde tendremos la informacion
        name = os.path.splitext(name_1)[0]  # Quitamos la extension
        words = name.split('_')

        p = words[2]
        f = words[4]

        self.label_20.setText(str(p) + ' cm')
        self.label_22.setText(f)
#########################################################################################################################################################################

# FUNCIONES PARA CAPTURA DE IMAGENES CON LA CAMARA
    def iniciar_toma_imagenes(self):
        print("a")

    def start_taking_pictures(self):
            


            global is_taking_pictures
            global picture_directory
            global ini


            #Asignamos color al texto que indica que se esta grabando
            self.label_16.setStyleSheet(f"color: #006400")
            self.label_16.setText('ALMACENANDO IMÁGENES')


            ini = False

            #Seelccionamos la carpeta donde se guardaran la simagenes. 
            picture_directory = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Picture Directory')


            #Creamos la carpeta Original si es que no existe. 

            if not os.path.exists(picture_directory + '/Original'):

                #Crea la carpeta de imagenes negativas
                os.makedirs(picture_directory + '/Original') 


            folder_original = picture_directory + '/Original'


            if picture_directory:
                self.picture_thread = VideoThread(folder_original)
                # Connect the signal to update the label with the video frame
                self.picture_thread.change_pixmap_signal.connect(self.update_video)
                
                # Start the picture thread
                self.picture_thread.start()

                is_taking_pictures = True    
    def stop_recording(self):

        self.label_16.setStyleSheet(f"color: #FF0000")
        self.label_16.setText('DETENIDO')
        global is_taking_pictures

        is_taking_pictures = False

        self.video_thread.stop()
        

#########################################################################################################################################################################
# FUNCIONES PARA CONTROLAR SLIDERS CON EL MANDO DE PS4


    def update_slider_btn(self, button):
            # scale the joystick value to the slider range
        global forward


        if button == 11: #BOTON AUMENTAR VELOCIDAD
            new_vel = self.velocidad_slider.value()

            new_vel = new_vel + 1

            if new_vel > 12:

                new_vel = 12

            #print (new_vel)

            self.velocidad_slider.setValue(new_vel)            


        if button == 12: #BOTON DISMINUIR VELOCIDAD
            new_vel = self.velocidad_slider.value()

            new_vel = new_vel - 1

            if new_vel < 0:

                new_vel = 0

            #print (new_vel)

            self.velocidad_slider.setValue(new_vel)

        if button == 3: #BOTON APAGAR LED
            self.btn_foco.setIcon(QtGui.QIcon(u"Iconos/off.png"))
            self.label_10.setText('OFF')
            self.label_10.setStyleSheet(f"color: #FF5154")

        if button == 2: #BOTON PRENDER LED
            self.btn_foco.setIcon(QtGui.QIcon(u"Iconos/on.png"))
            self.label_10.setText('ON')
            self.label_10.setStyleSheet(f"color: #006400")




        if forward == 1:
                
                self.label_25.setText('AVANCE')
                self.label_25.setStyleSheet(f"color: #006400")

                

        if forward == -1 :

                
                self.label_25.setText('RETROCESO')
                self.label_25.setStyleSheet(f"color: #FF5154")


        if forward == 0 :
              
                self.label_25.setText('DETENIDO')
                self.label_25.setStyleSheet(f"color: #000000")

    def receive (self, data):

            global d_prev
            global distancia_abs
            global f_d
            global posicion_label
            global primera_vez
            global reiniciar_flag

            r = 1
            nd = 20.0

            data = data.replace('$OAX1jb','')
            encoder = round((2*3.1415*r)*(float(data)/nd),2)
            
            #print ('Lectura Encoder:' + str(encoder))

            posicion_label = str(round(encoder,2))

            #print ('Label:' + posicion_label)
    
            self.label_7.setText(posicion_label + 'cm')
            self.posicion_slider.setValue(int(encoder))

            distancia_abs = encoder


    def update_slider(self, value, axis):
        # scale the joystick value to the slider range
        global angv 
        global angh


        if axis == 3:
             
            x = 1
            
            

        if axis == 0:


            scaled_value = int(value)

            if scaled_value >= 0.3:
                angh = angh + 10

            if scaled_value < -0.3:
                angh = angh - 10

            if angh > 90:
                angh = 90

            if angh < -90:
                angh = -90

            

            self.anguloh_slider.setValue(int(angh))




        if axis == 1:

            
            scaled_value = int(value)

            if scaled_value >= 0.3:
                angv = angv - 10

            if scaled_value < -0.3:
                angv = angv + 10

            if angv > 90:
                angv = 90

            if angv < -90:
                angv = -90

            

            self.angulov_slider.setValue(int(angv))

    def closeEvent(self, event):
        # stop the controller thread when the main window is closed
        self.controller_thread.stop()
        self.controller_thread.wait()
        event.accept()



    def update_angulov(self,event):

        self.label_6.setText(str(event) + '°')

        if event == 0:
                ang = 0

        if  0 < abs(event) <= 5:
            ang = 5
        if  6 <= abs(event) <= 10:
            ang = 10
        if  11 <= abs(event) <= 15:
            ang = 15
        if  16 <= abs(event) <= 20:
            ang = 20
        if  21 <= abs(event) <= 25:
            ang = 25     
        if  26 <= abs(event) <= 30:
            ang = 30
        if  31 <= abs(event) <= 35:
            ang = 35
        if  36 <= abs(event) <= 40:
            ang = 40
        if  41 <= abs(event) <= 45:
            ang = 45                   
        if  46 <= abs(event) <= 50:
            ang = 50
        if  51 <= abs(event) <= 55:
            ang = 55
        if  56 <= abs(event) <= 60:
            ang = 60
        if  61 <= abs(event) <= 65:
            ang = 65     
        if  66 <= abs(event) <= 70:
            ang = 70
        if  71 <= abs(event) <= 75:
            ang = 75
        if  76 <= abs(event) <= 80:
            ang = 80
        if  81 <= abs(event) <= 85:
            ang = 85        
        if  86 <= abs(event) <= 90:
            ang = 90


        if event >= 0:
            self.btn_angv.setIcon(QtGui.QIcon(u"angulosv/"+str(ang)+'.png'))
            print(ang)

        else:
            self.btn_angv.setIcon(QtGui.QIcon(u"angulosv/-"+str(ang)+'.png'))
            print(ang)

    def update_anguloh(self,event):

        self.label_15.setText(str(event) + '°')

        if event == 0:
                ang = 0

        if  0 < abs(event) <= 5:
            ang = 5
        if  6 <= abs(event) <= 10:
            ang = 10
        if  11 <= abs(event) <= 15:
            ang = 15
        if  16 <= abs(event) <= 20:
            ang = 20
        if  21 <= abs(event) <= 25:
            ang = 25     
        if  26 <= abs(event) <= 30:
            ang = 30
        if  31 <= abs(event) <= 35:
            ang = 35
        if  36 <= abs(event) <= 40:
            ang = 40
        if  41 <= abs(event) <= 45:
            ang = 45                   
        if  46 <= abs(event) <= 50:
            ang = 50
        if  51 <= abs(event) <= 55:
            ang = 55
        if  56 <= abs(event) <= 60:
            ang = 60
        if  61 <= abs(event) <= 65:
            ang = 65     
        if  66 <= abs(event) <= 70:
            ang = 70
        if  71 <= abs(event) <= 75:
            ang = 75
        if  76 <= abs(event) <= 80:
            ang = 80
        if  81 <= abs(event) <= 85:
            ang = 85        
        if  86 <= abs(event) <= 90:
            ang = 90


        if event >= 0:
            self.btn_angh.setIcon(QtGui.QIcon(u"angulos/"+str(ang)+'.png'))
            print(ang)

        else:
            self.btn_angh.setIcon(QtGui.QIcon(u"angulos/-"+str(ang)+'.png'))
            print(ang)


    

    def update_velocidad(self,event):

        self.label_13.setText('Velocidad ' + str(event))


#########################################################################################################################################################################
# FUNCION PARA AGRANDAR Y ACHICAR LA SENAL DE VIDEO AL AGRANDAR Y ACHICAR LA PANTALLA

    def update_video(self, buffer):
        # Load the image from bytes
        pixmap = QPixmap()
        pixmap.loadFromData(buffer)

        # Set the pixmap on the label
        self.VisionCamara.setPixmap(pixmap)


    def maximize_video(self):
        global height
        global width

        height = 540

        width = 960

    def minimize_video(self):
        global height
        global width

        height = 540
        width = 960


    def closeEvent(self, event):
        # Stop the video thread before closing the window
        self.video_thread.stop()
        self.video_thread.wait()
        super().closeEvent(event)

        
#########################################################################################################################################################################
# FUNCION PARA REAJUSTAR DISTRIBUCION DE FUNCIONES EN LA PANTALLA PRINCIPAL

    #Funcion que distribuye funcion de posicion, control y angulos
    def loadSTLModel(self):

        stl_reader = vtk.vtkSTLReader()
        stl_reader.SetFileName("afton.stl")  # Reemplaza con la ruta de tu archivo STL

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(stl_reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()

        self.iren.Initialize()
        self.iren.Start() 
    def distribuir (self):

    #################################################################
    # Distribucion espacio
        self.main_body_left.setMaximumSize(10000,10000)
        self.frame_left_up.setMaximumSize(100000,1000000)
        self.frame_camara.setMaximumSize(0,0)
        self.frame_angulo.setMaximumSize(10000,10000)
        self.frame_control.setMaximumSize(0,0)

        self.frame_archivos.setMaximumSize(0,0)

        self.main_body_right.setMaximumSize(0,10000000)
       
        self.frame_position.setMaximumSize(0,0)

        self.frame_fondo.setMaximumSize(1000000,0)

        self.VisionCamara.setMinimumSize(0,0)
        


        font3 = QFont()
        font3.setPointSize(7)
        font3.setBold(True)
        font3.setWeight(75)
        self.label_3.setFont(font3)
    #################################################################

    def distribuir_posicion (self):

    #################################################################
    # Distribucion espacio
        self.main_body_left.setMaximumSize(0,0000)
        self.main_body_right.setMaximumSize(100000,10000)
        self.frame_fondo.setMaximumSize(0,0)
        self.frame_camara.setMaximumSize(0,0)
        self.frame_angulo.setMaximumSize(0,00)
        self.frame_control.setMaximumSize(0,0)
        self.frame_archivos.setMaximumSize(0,0)
        self.frame_position.setMaximumSize(100000,1000000)


        self.VisionCamara.setMinimumSize(0,0)


        font3 = QFont()
        font3.setPointSize(7)
        font3.setBold(True)
        font3.setWeight(75)
        self.label_3.setFont(font3)
    #################################################################

    def distribuir_control (self):

    #################################################################
    # Distribucion espacio
        self.main_body_left.setMaximumSize(10000,10000)

        self.frame_camara.setMaximumSize(0,0)
        self.frame_angulo.setMaximumSize(0,0)
        self.frame_control.setMaximumSize(0,0)
        ## El frame_archivos realmente se refiere al frame_control
        self.frame_archivos.setMaximumSize(600000000,1000000)
        self.framefoco.setMaximumSize(0,0)
        self.frame_left_up.setMaximumSize(0,0)

        self.main_body_right.setMaximumSize(0,0)
        self.frame_position.setMaximumSize(0,0)
        self.frame_fondo.setMaximumSize(0,0)

        self.VisionCamara.setMinimumSize(0,0) 
       
    #################################################################
    #Funcion que distribuye funcion de camara
    def distribuir_camara (self):

        self.main_body_left.setMaximumSize(1000000,10000000)

        self.frame_camara.setMaximumSize(1000000,100000)
        self.frame_angulo.setMaximumSize(0,0)
        self.frame_control.setMaximumSize(0,0)
        self.frame_archivos.setMaximumSize(0,0)

        self.frame_left_up.setMaximumSize(1000000,1000000)

        
        self.VisionCamara.setMinimumSize(960,540)
        self.VisionCamara.setMaximumSize(960,540)
###############################################
        self.main_body_right.setMaximumSize(0,0)
       
        self.frame_position.setMaximumSize(0,0)
        self.frame_fondo.setMaximumSize(0,0)
        self.framefoco.setMaximumSize(0,0)
         
    #Funcion que distribuye funcion de archivos
    def distribuir_archivos (self):
 
       self.main_body_left.setMaximumSize(10000,10000)

       self.frame_camara.setMaximumSize(0,0)
       self.frame_angulo.setMaximumSize(0,0)
       self.frame_control.setMaximumSize(100000,100000)
       self.frame_archivos.setMaximumSize(0,0)
       self.framefoco.setMaximumSize(0,0)
       self.label_24.setMinimumSize(960,540)

       self.label_24.setMaximumSize(960,540)

       self.main_body_right.setMaximumSize(0,0)
       
       self.frame_position.setMaximumSize(0,0)

       self.frame_fondo.setMaximumSize(0,0)

    #Funcion para reiniciar distribucion de espacios
    def reset_button (self):
        self.main_body_left.setMaximumSize(0,0)
        self.frame_position.setMaximumSize(10000000,0)

        self.main_body_right.setMaximumSize(100000,100000)
##############################################################
        self.frame_fondo.setMaximumSize(100000,100000)
        self.frame_imagen_pype.setMaximumSize(100000000,30000000)
        self.frame_logo.setMaximumSize(100000000,200)
        self.label_3.setMaximumSize(100000000,200000000)
###############################################################
        self.frame_camara.setMaximumSize(0,0)
        self.frame_angulo.setMaximumSize(0,0)
        self.frame_control.setMaximumSize(0,0)
        self.frame_archivos.setMaximumSize(0,0)


        font3 = QFont()
        font3.setPointSize(48)
        font3.setBold(True)
        font3.setWeight(75)
        self.label_3.setFont(font3)


#########################################################################################################################################################################
# FUNCION MENU DESLIZANTE


    def slideLeftMenu(self):
        #Obtenemos la medida del ancho del menu
        width = self.slide_menu_container.width()

        # Si esta minimized
        if width == 0:
            # Expand menu
            newWidth = 300

            self.open_close_side_bar_btn.setIcon(QtGui.QIcon(u"Iconos/left.png"))


        # Si el menu esta abierto
        else:
            # Restore menu
            newWidth = 0

            self.open_close_side_bar_btn.setIcon(QtGui.QIcon(u"Iconos/menu.png"))


        # Transision de animacion
        self.animation = QPropertyAnimation(self.slide_menu_container, b"maximumWidth")#Animate minimumWidht
        self.animation.setDuration(250)
        self.animation.setStartValue(width)#Start value is the current menu width
        self.animation.setEndValue(newWidth)#end value is the new menu width
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()




#########################################################################################################################################################################
# FUNCION MOVER VENTANA

    # Evento de mouse
    def mousePressEvent(self, event):
        # Get the current position of the mouse
        self.clickPosition = event.globalPos()
        # We will use this value to move the window
#########################################################################################################################################################################
# PANTALLA DE CARGA

class MiApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MiApp,self).__init__()

        #Cargamos ventana de carga
        loadUi('src/GUI/pochita.ui',self)

        #Quitamos el borde y adicionamos fondo transparente
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1)

                ## QTIMER ==> START
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)
        # TIMER CADA 3 MS
        self.timer.start(3)




    # Funcion que anima barra de carga
    def progress(self):

        global counter

        # OTORGAMOS VALOR A LA BARRA DE CARGA
        self.progressBar.setValue(counter)

        # DETERMINAMOS EL CONTEO MAXIMO
        if counter > 100:
            # STOP TIMER
            self.timer.stop()

            # SHOW MOSTRAR PANTALLA PRINCIPAL
            self.main = MainPage()
            self.main.show()


            # CLOSE SPLASH SCREEN
            self.close()

        # INCREMENTAMOS CONTADOR
        counter += 1



#########################################################################################################################################################################
# FIN DE LA SECUENCIA

if __name__ == "__main__":
     app = QtWidgets.QApplication(sys.argv)
     ex = QtWidgets.QFileDialog()
    
     mi_app = MiApp()
     mi_app.show()
     mi_app.progress()

     sys.exit(app.exec_())	


     