import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import pyautogui
import time
import threading
import os
import sys
import datetime

APP_TITLE = "Keep Active App"
LOG_FILE = "keep_active.log"
ICON_FILE = "KA_icon.ico"

stop_flag = False
worker_thread = None
proc_notepad = None
blink_state = True  # para animación del cronómetro

# ---------------- LOG ----------------

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass

# ---------------- LÓGICA PRINCIPAL ----------------

def ejecutar_script():
    global stop_flag, worker_thread
    try:
        minutos = int(entry_tiempo.get())
    except ValueError:
        label_estado.config(text="Introduce un número válido")
        messagebox.showerror("Error", "Introduce un número válido de minutos.")
        return

    if minutos <= 0:
        label_estado.config(text="Minutos > 0")
        messagebox.showerror("Error", "La duración debe ser mayor que 0.")
        return

    duracion_segundos = minutos * 60
    stop_flag = False
    label_estado.config(text="Ejecutando...")
    modo = modo_var.get()
    log(f"Iniciando: {minutos} min, modo: {modo}")

    worker_thread = threading.Thread(
        target=run_worker,
        args=(duracion_segundos, modo),
        daemon=True
    )
    worker_thread.start()

    actualizar_contador(duracion_segundos)

def run_worker(duracion, modo):
    global stop_flag, proc_notepad

    if stop_flag:
        return

    if modo == "Notepad":
        log("Modo Notepad: abriendo Bloc de notas")
        proc_notepad = subprocess.Popen("notepad.exe")
        time.sleep(1.5)

        pyautogui.press('alt')
        time.sleep(0.2)

        inicio = time.time()
        while time.time() - inicio < duracion:
            if stop_flag:
                log("Stop recibido en modo Notepad")
                break
            pyautogui.press('right')
            time.sleep(0.3)

        cerrar_notepad()
        log("Modo Notepad finalizado")

    elif modo == "Teams":
        log("Modo Teams: actividad discreta")
        inicio = time.time()
        toggle = True
        while time.time() - inicio < duracion:
            if stop_flag:
                log("Stop recibido en modo Teams")
                break

            x, y = pyautogui.position()
            pyautogui.moveTo(x + (1 if toggle else -1), y)
            toggle = not toggle

            pyautogui.keyDown('shift')
            time.sleep(0.05)
            pyautogui.keyUp('shift')

            time.sleep(30)

        log("Modo Teams finalizado")

    root.after(0, fin_ejecucion_ui)

def fin_ejecucion_ui():
    label_estado.config(text="Finalizado")
    boton_startstop.config(text="Iniciar")

def actualizar_contador(restante):
    global blink_state

    if stop_flag:
        label_contador.config(text="00:00")
        return

    minutos = restante // 60
    segundos = restante % 60
    label_contador.config(text=f"{minutos:02d}:{segundos:02d}")

    # Animación: parpadeo suave
    if blink_state:
        label_contador.configure(foreground="#00aa66")
    else:
        label_contador.configure(foreground="#44dd99")
    blink_state = not blink_state

    if restante > 0:
        root.after(1000, actualizar_contador, restante - 1)
    else:
        log("Contador terminado")

def detener():
    global stop_flag
    stop_flag = True
    label_estado.config(text="Deteniendo...")
    log("Detener pulsado")
    cerrar_notepad()
    boton_startstop.config(text="Iniciar")

def cerrar_notepad():
    global proc_notepad
    if proc_notepad:
        try:
            proc_notepad.terminate()
            log("Notepad terminado")
        except:
            log("Error al terminar Notepad")
        proc_notepad = None

# ---------------- CIERRE ----------------

def on_close():
    global stop_flag, worker_thread
    stop_flag = True
    cerrar_notepad()
    log("Cerrando aplicación")

    if worker_thread and worker_thread.is_alive():
        worker_thread.join(timeout=1)

    root.destroy()

# ---------------- BOTÓN DINÁMICO ----------------

def toggle_start_stop():
    if boton_startstop["text"] == "Iniciar":
        ejecutar_script()
        boton_startstop.config(text="Detener")
    else:
        detener()
        boton_startstop.config(text="Iniciar")

# ---------------- INTERFAZ ----------------

root = tk.Tk()
root.title(APP_TITLE)
root.geometry("360x340")  # ventana más alta

# ---------------- ICONO COMPATIBLE .PYW + .EXE ----------------

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(BASE_DIR, ICON_FILE)

if os.path.exists(icon_path):
    try:
        root.iconbitmap(icon_path)
        log(f"Icono cargado: {icon_path}")
    except Exception as e:
        log(f"No se pudo cargar el icono: {e}")
else:
    log(f"Icono no encontrado en: {icon_path}")

# ---------------- UI ----------------

frame_main = ttk.Frame(root, padding=10)
frame_main.pack(fill="both", expand=True)

label_modo = ttk.Label(frame_main, text="Modo:")
label_modo.pack(pady=2)

modo_var = tk.StringVar(value="Notepad")
combo_modo = ttk.Combobox(
    frame_main,
    textvariable=modo_var,
    state="readonly",
    values=["Notepad", "Teams"]
)
combo_modo.pack(pady=2)

label = ttk.Label(frame_main, text="Duración en minutos:")
label.pack(pady=5)

entry_tiempo = ttk.Entry(frame_main, justify="center")
entry_tiempo.insert(0, "5")
entry_tiempo.pack(pady=5)

boton_startstop = ttk.Button(frame_main, text="Iniciar", command=toggle_start_stop)
boton_startstop.pack(pady=10)

label_contador = ttk.Label(frame_main, text="00:00", font=("Arial", 26))
label_contador.pack(pady=15)

label_estado = ttk.Label(frame_main, text="")
label_estado.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)

log("Aplicación iniciada")
root.mainloop()
