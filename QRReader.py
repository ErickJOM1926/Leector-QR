import cv2;  # Importa la biblioteca OpenCV para procesamiento de imágenes
import numpy as np;  # Importa numpy para trabajar con matrices
from pyzbar.pyzbar import decode  # Importa pyzbar para decodificar códigos QR
import sqlite3  # Importa sqlite3 para la gestión de la base de datos SQLite
from twilio.rest import Client  # Importa la biblioteca Twilio para enviar mensajes SMS/WhatsApp

# Conecta a la base de datos SQLite
conn = sqlite3.connect("qr_database.db")
cursor = conn.cursor()

# Crea una tabla en la base de datos si no existe
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS qr_codes (
        id INTEGER PRIMARY KEY,
        data TEXT
    )
"""
)

# Configuración de Twilio para enviar mensajes
account_sid = "ACa0c163f3221e3b4859dcf32ca35b8dba"
auth_token = "c3511523506b2071f2d942bf408e8f9c"
client = Client(account_sid, auth_token)

# Inicializa la cámara usando OpenCV
cap = cv2.VideoCapture(0)

# Bucle principal para capturar imágenes de la cámara
while True:
    success, img = cap.read()  # Captura una imagen desde la cámara

    if not success:  # Si no se pudo capturar una imagen, sale del bucle
        break

    for code in decode(img):  # Decodifica códigos QR en la imagen
        decoded_data = code.data.decode("utf-8")  # Obtiene los datos decodificados

        rect_pts = code.rect  # Obtiene los puntos del rectángulo alrededor del código QR

        if decoded_data:
            cursor.execute("SELECT id FROM qr_codes WHERE data=?", (decoded_data,))
            existing_entry = cursor.fetchone()

            if existing_entry is None:
                # Si el código QR no existe en la base de datos, lo agrega
                cursor.execute(
                    "INSERT INTO qr_codes (data) VALUES (?)", (decoded_data,)
                )
                conn.commit()
            else:
                # Si el código QR ya existe en la base de datos, envía un mensaje con Twilio
                message = client.messages.create(
                    body=f"Información existente en la base de datos: {decoded_data}",
                    from_="whatsapp:+14155238886",
                    to="whatsapp:+5215582236747",
                )

            pts = np.array([code.polygon], np.int32)
            cv2.polylines(img, [pts], isClosed=True, color=(255, 0, 0), thickness=3)
            cv2.putText(
                img,
                str(decoded_data),
                (rect_pts[0], rect_pts[1] - 10),
                cv2.FONT_HERSHEY_COMPLEX_SMALL,
                1,
                (0, 255, 0),
                2,
            )

    cv2.imshow("image", img)  # Muestra la imagen con los códigos QR marcados
    if cv2.waitKey(1) & 0xFF == 27:  # Presiona 'Esc' para apagar la cámara
        break

cap.release()  # Libera la cámara
cv2.destroyAllWindows()  # Cierra la ventana de visualización de OpenCV

conn.close()  # Cierra la conexión a la base de datos
