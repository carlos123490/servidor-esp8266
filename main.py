from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Definimos qué datos esperamos recibir del ESP8266
class DatosSensor(BaseModel):
    temperatura: float
    humedad: float

@app.get("/")
def inicio():
    return {"mensaje": "Servidor IA funcionando correctamente"}

@app.post("/prediccion")
def procesar_datos(datos: DatosSensor):
    # Aquí puedes añadir tu modelo de IA en el futuro.
    # Por ahora, usamos una lógica simple de ejemplo:
    if datos.temperatura > 30.0:
        accion = "ENCENDER_VENTILADOR"
    else:
        accion = "MANTENER_APAGADO"
        
    return {
        "status": "ok",
        "alerta": datos.temperatura > 30.0,
        "comando": accion
    }