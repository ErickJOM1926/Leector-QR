import cv2
import numpy as np
from pyzbar.pyzbar import decode
import sqlite3
from twilio.rest import Client

# Configuración (coloca tus propios valores aquí)
TWILIO_ACCOUNT_SID = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # SID de tu cuenta Twilio
TWILIO_AUTH_TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Token de autenticación de Twilio
TWILIO_FROM_NUMBER = "whatsapp:+14155238886"  # Número de WhatsApp desde el que enviarás mensajes
TWILIO_TO_NUMBER = "whatsapp:+5215544332211"  # Número de WhatsApp de destino

def conectar_base_de_datos():
    # Conecta a la base de datos SQLite y crea la tabla si no existe
    conn = sqlite3.connect("qr_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_codes (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    return conn, cursor

def cerrar_base_de_datos(conn):
    conn.close()

def leer_codigo_qr(conn, cursor):
    cap = cv2.VideoCapture(0)  # Inicializa la cámara
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)  # Inicializa el cliente Twilio

    while True:
        success, img = cap.read()  # Captura una imagen desde la cámara

        if not success:
            break

        for code in decode(img):  # Decodifica códigos QR en la imagen
            decoded_data = code.data.decode("utf-8")  # Obtiene los datos decodificados
            rect_pts = code.rect  # Obtiene los puntos del rectángulo alrededor del código QR

            if decoded_data:
                cursor.execute("SELECT id FROM qr_codes WHERE data=?", (decoded_data,))
                existing_entry = cursor.fetchone()

                if existing_entry is None:
                    cursor.execute("INSERT INTO qr_codes (data) VALUES (?)", (decoded_data,))
                    conn.commit()
                else:
                    message = client.messages.create(
                        body=f"Información existente en la base de datos: {decoded_data}",
                        from_=TWILIO_FROM_NUMBER,
                        to=TWILIO_TO_NUMBER,
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

if __name__ == "__main__":
    conn, cursor = conectar_base_de_datos()
    leer_codigo_qr(conn, cursor)
    cerrar_base_de_datos(conn)
