from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import json

app = FastAPI()

# --- ESTADO GLOBAL EN LA NUBE ---
estado_invernadero = {
    "hora": "--:--:--",
    "temp": 0.0,
    "ntp": False,
    "disp": [
        {"nombre": "Bomba 1", "modo": 0, "estado": 0, "rest": 0, "tmin": 20.0, "tmax": 30.0, "hmin": 1500, "hmax": 3000, "ph": 6, "pm": 0, "duracion": 600},
        {"nombre": "Ventilador", "modo": 0, "estado": 0, "rest": 0, "tmin": 20.0, "tmax": 30.0, "hmin": 1500, "hmax": 3000, "ph": 6, "pm": 0, "duracion": 600},
        {"nombre": "Luz UV", "modo": 0, "estado": 0, "rest": 0, "tmin": 20.0, "tmax": 30.0, "hmin": 1500, "hmax": 3000, "ph": 6, "pm": 0, "duracion": 600},
        {"nombre": "Riego 2", "modo": 0, "estado": 0, "rest": 0, "tmin": 20.0, "tmax": 30.0, "hmin": 1500, "hmax": 3000, "ph": 6, "pm": 0, "duracion": 600}
    ]
}

comandos_pendientes = []

class DatosSensor(BaseModel):
    temperatura: float
    humedad: float

# --- INTERFAZ WEB INTERACTIVA (Misma estética que la local) ---
@app.get("/", response_class=HTMLResponse)
async def home_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invernadero Cloud Global</title>
    <style>
      :root {
        --bg:#0f172a; --card:#1e293b; --cardOn:#0d2818; --border:#334155;
        --green:#22c55e; --red:#ef4444; --blue:#3b82f6; --yellow:#eab308; --purple:#a855f7;
        --text:#e2e8f0; --text2:#94a3b8;
      }
      *{box-sizing:border-box;margin:0;padding:0}
      body{font-family:system-ui,Arial;background:var(--bg);color:var(--text);padding:12px;}
      .header{text-align:center;margin-bottom:16px}
      .header h2{font-size:1.8rem;margin-bottom:8px}
      .stats{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:16px}
      .stat{background:var(--card);padding:10px 16px;border-radius:12px;border:1px solid var(--border)}
      .stat span{font-size:1.4rem;font-weight:600}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}
      .card{background:var(--card);border:2px solid var(--border);border-radius:16px;padding:16px;transition:.2s}
      .card.on{border-color:var(--green);background:var(--cardOn)}
      .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px}
      .name-input{background:transparent;border:1px dashed var(--border);color:var(--text);padding:4px 8px;border-radius:6px;font-size:1.1rem;font-weight:600;width:100%}
      .badge{padding:4px 10px;border-radius:20px;font-size:.75rem;font-weight:600;white-space:nowrap}
      .b-manual{background:#64748b}.b-temp{background:var(--red)}.b-hum{background:var(--blue)}
      .b-timer{background:var(--yellow);color:#000}.b-prog{background:var(--purple)}
      .estado{font-size:.9rem;color:var(--text2);margin-bottom:12px}
      .estado.on{color:var(--green);font-weight:600}
      .btn-group{display:flex;gap:8px;margin-bottom:12px}
      button{flex:1;padding:10px;border:none;border-radius:8px;font-weight:600;cursor:pointer;transition:.15s}
      button:active{transform:scale(.96)}
      .btn-on{background:var(--green);color:#000}.btn-off{background:var(--red);color:#fff}
      .btn-ctrl{background:var(--blue);color:#fff}
      .timer{font-family:monospace;font-size:1.6rem;text-align:center;background:#000;padding:8px;border-radius:8px;margin:12px 0}
      .section{margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}
      .section h4{font-size:.85rem;color:var(--text2);margin-bottom:8px;text-transform:uppercase}
      .input-group,.hms-group{display:grid;grid-template-columns:auto 1fr auto 1fr;gap:8px;align-items:center;margin-bottom:8px}
      input[type=number]{width:100%;background:#0f172a;border:1px solid var(--border);color:var(--text);padding:8px;border-radius:6px;text-align:center}
    </style>
    </head>
    <body>
    <div class="header">
      <h2>🌍 INVERNADERO GLOBAL INTERNET</h2>
      <div class="stats">
        <div class="stat">🕒 Hora ESP32: <span id="hora">--:--:--</span></div>
        <div class="stat">🌡️ Temperatura: <span id="temp">--.-</span>°C</div>
        <div class="stat">NTP: <span id="ntp">SYNC</span></div>
      </div>
    </div>
    <div class="grid" id="contenedor"></div>

    <script>
    let inicializado = false;
    const modos = [
      {txt:"MANUAL", cls:"b-manual"}, {txt:"TEMP", cls:"b-temp"},
      {txt:"HUMEDAD", cls:"b-hum"}, {txt:"TIMER", cls:"b-timer"},
      {txt:"PROGRAM", cls:"b-prog"}
    ];

    function cargar(){
      fetch("/cloud-data").then(r=>r.json()).then(d=>{
        document.getElementById("hora").innerText=d.hora;
        document.getElementById("temp").innerText=d.temp;
        document.getElementById("ntp").innerText=d.ntp?"OK":"SYNC";
        
        let c=document.getElementById("contenedor");
        if(!inicializado){
          c.innerHTML="";
          d.disp.forEach((p,i)=>{
            let restSegundos = p.rest || 0;
            c.innerHTML+=`
              <div class="card" id="card${i}">
                <div class="card-header">
                  <input class="name-input" id="nombre${i}" value="${p.nombre}" onchange="enviarCmd(${i},'nombre',this.value)">
                  <span class="badge ${modos[p.modo].cls}" id="badge${i}">${modos[p.modo].txt}</span>
                </div>
                <div class="estado" id="estado${i}">${p.estado?'● ENCENDIDO':'○ APAGADO'}</div>
                <div class="btn-group">
                  <button class="btn-on" onclick="enviarCmd(${i},'manual',1)">ON</button>
                  <button class="btn-off" onclick="enviarCmd(${i},'manual',0)">OFF</button>
                </div>
                <div class="timer" id="timer${i}">${formato(restSegundos)}</div>
                <div class="btn-group">
                  <button class="btn-ctrl" onclick="enviarCmd(${i},'start',1)">▶ START</button>
                  <button class="btn-ctrl" onclick="enviarCmd(${i},'stop',1)">■ STOP</button>
                </div>
                <div class="section">
                  <h4>Configurar Timer</h4>
                  <div class="hms-group">
                    <input type="number" id="m${i}" value="${Math.floor(restSegundos/60)}" placeholder="Minutos">
                    <button class="btn-ctrl" onclick="setTimer(${i})">Set</button>
                  </div>
                </div>
              </div>`;
          });
          inicializado = true;
        } else {
          d.disp.forEach((p,i)=>{
            let card = document.getElementById(`card${i}`);
            if(card){
              card.className = `card ${p.estado?'on':''}`;
              document.getElementById(`badge${i}`).className = `badge ${modos[p.modo].cls}`;
              document.getElementById(`badge`+i).innerText = modos[p.modo].txt;
              document.getElementById(`estado`+i).innerText = p.estado?'● ENCENDIDO':'○ APAGADO';
              document.getElementById(`timer`+i).innerText = formato(p.rest || 0);
            }
          });
        }
      });
    }

    function enviarCmd(pin, accion, valor){
      fetch(`/enviar-comando?pin=${pin}&accion=${accion}&valor=${encodeURIComponent(valor)}`);
    }
     Hellenic = false;
    function setTimer(i){
      let m = parseInt(document.getElementById("m"+i).value)||0;
      enviarCmd(i, 'timer', (m*60));
    }
    function formato(s){
      let h=Math.floor(s/3600); let m=Math.floor((s%3600)/60); let sec=s%60;
      return (h<10?"0":"")+h+":"+(m<10?"0":"")+m+":"+(sec<10?"0":"")+sec;
    }
    setInterval(cargar, 2000);
    window.onload = cargar;
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/cloud-data")
async def obtener_datos_nube():
    return JSONResponse(content=estado_invernadero)

@app.get("/enviar-comando")
async def enviar_comando(pin: int, accion: str, valor: str):
    global comandos_pendientes
    comando = {"pin": pin, "accion": accion, "valor": valor}
    comandos_pendientes.append(comando)
    return {"status": "ok", "msg": "Comando en cola listo"}

@app.post("/prediccion")
async def procesar_datos_esp32(datos: DatosSensor):
    global comandos_pendientes, estado_invernadero
    estado_invernadero["temp"] = datos.temperatura
    cmds_a_enviar = list(comandos_pendientes)
    comandos_pendientes.clear()
    return {"status": "ok", "comandos": cmds_a_enviar}

@app.post("/sync-completo")
async def sync_completo(request: Request):
    global estado_invernadero
    try:
        body = await request.body()
        datos_recibidos = json.loads(body.decode("utf-8", errors="ignore"))
        
        if "hora" in datos_recibidos: estado_invernadero["hora"] = datos_recibidos["hora"]
        if "temp" in datos_recibidos: estado_invernadero["temp"] = datos_recibidos["temp"]
        
        # Procesamiento ultra-flexible para los estados de los relés
        if "disp" in datos_recibidos and isinstance(datos_recibidos["disp"], list):
            for i, d in enumerate(datos_recibidos["disp"]):
                if i < len(estado_invernadero["disp"]):
                    if "estado" in d: estado_invernadero["disp"][i]["estado"] = d["estado"]
                    if "modo" in d: estado_invernadero["disp"][i]["modo"] = d["modo"]
                    if "nombre" in d: estado_invernadero["disp"][i]["nombre"] = d["nombre"]
                    
                    # Buscador tolerante para la variable de tiempo restante (rest)
                    for clave_llave in d.keys():
                        if "rest" in clave_llave:
                            estado_invernadero["disp"][i]["rest"] = d[clave_llave]
    except Exception as e:
        print(f"Error en sincronización Cloud: {e}")
        
    return {"status": "sync_ok"}
