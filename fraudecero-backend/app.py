import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

client = None
try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI listo.")
    else:
        print("⚠️ Falta API Key.")
except Exception as e:
    print(f"❌ Error config: {e}")

# PROMPT MEJORADO (Detecta contexto de dinero y ve imágenes)
SYSTEM_PROMPT = """
Eres "Fraudecero", analista de ciberseguridad.
Analiza texto o imágenes para detectar estafas.

Responde SOLO JSON:
{"riesgo": "ALTO", "razon": "Breve explicación"} 
o 
{"riesgo": "BAJO", "razon": "Breve explicación"}

REGLAS:
1. "DINERO/PLATA" EN CHARLA CASUAL (amigos, familia, montos bajos) = RIESGO BAJO 🟢.
2. RIESGO ALTO 🔴: Urgencia, links raros, desconocidos pidiendo plata, premios falsos, logos pixelados.
"""

@app.route('/', methods=['GET'])
def home():
    return "🤖 Fraudecero v2.0 Activo"

@app.route('/check', methods=['POST'])
def check_fraud():
    if not client:
        return jsonify({"status": "error", "message": "Sin API Key"}), 500
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Sin datos"}), 400

    texto = data.get('text', '')
    imagen = data.get('image', None)

    print(f"📩 Recibido. Texto: {texto} | Imagen: {'SÍ' if imagen else 'NO'}")

    user_content = []
    if texto: user_content.append({"type": "text", "text": texto})
    if imagen: user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen}"}})

    if not user_content:
        return jsonify({"status": "error", "message": "Envía algo"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.0
        )
        
        resultado = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return jsonify({"status": "success", "analysis": resultado})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
