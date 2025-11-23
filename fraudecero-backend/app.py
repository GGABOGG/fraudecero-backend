import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS  # <--- NUEVO

load_dotenv()

app = Flask(__name__)
CORS(app)  



# Cargar variables si estamos en local (en Render esto no hace daño)
load_dotenv()

app = Flask(__name__)

# --- Configuración de OpenAI ---
client = None
try:
    # Intenta obtener la clave
    api_key = os.environ.get('OPENAI_API_KEY')
    
    # Si no hay clave, imprimimos advertencia pero no rompemos la app todavía
    if not api_key:
        print("⚠️ ADVERTENCIA: No se encontró OPENAI_API_KEY.")
    else:
        client = OpenAI(api_key=api_key)
        print("✅ Cliente OpenAI configurado exitosamente.")

except Exception as e:
    print(f"❌ Error al configurar OpenAI: {e}")

# EL PROMPT: La instrucción maestra
SYSTEM_PROMPT = """
Eres "Fraudecero", un experto en ciberseguridad.
Analiza el mensaje y responde ÚNICAMENTE con un JSON que tenga este formato:
{"riesgo": "ALTO", "razon": "Explicación breve"} 
o 
{"riesgo": "BAJO", "razon": "Explicación breve"}

Si es phishing, estafa, o pide dinero/datos urgentes, el riesgo es ALTO.
"""

@app.route('/', methods=['GET'])
def home():
    return "🤖 Fraudecero API está activa y funcionando."

@app.route('/check', methods=['POST'])
def check_text():
    # 1. Verificar si tenemos el cerebro conectado
    if not client:
        return jsonify({"status": "error", "message": "El servidor no tiene configurada la API Key de OpenAI."}), 500
    
    # 2. Obtener el texto del celular
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "Falta el campo 'text' en el JSON"}), 400
    
    mensaje_usuario = data['text']
    print(f"📩 Analizando: {mensaje_usuario}")

    try:
        # 3. Consultar a la IA
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensaje_usuario}
            ],
            temperature=0.0
        )
        
        # 4. Leer respuesta de la IA
        resultado_ia = response.choices[0].message.content
        print(f"🤖 Dice: {resultado_ia}")

        # Devolver tal cual lo que dijo la IA
        return jsonify({"status": "success", "analysis": resultado_ia})

    except Exception as e:
        print(f"❌ Error al conectar con OpenAI: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Esto permite correrlo en tu PC
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)