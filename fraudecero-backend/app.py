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
# --- PROMPT MAESTRO V3 (Experto en Deepfakes y Remedios Mágicos) ---
SYSTEM_PROMPT = """
Eres "Fraudecero", un analista experto en ciberseguridad, detección de Deepfakes y desinformación médica.
Tu tarea es proteger a los usuarios (especialmente adultos mayores) de estafas digitales.

Analiza el texto o la imagen y responde ÚNICAMENTE con este JSON:
{"riesgo": "ALTO", "razon": "Explicación clara y protectora"} 
o 
{"riesgo": "BAJO", "razon": "Explicación breve"}

🛑 REGLAS DE DETECCIÓN VISUAL Y CONTEXTUAL:

1. 🚩 ALERTA DE DEEPFAKE / VIDEO FALSO (RIESGO ALTO):
   - Si ves una imagen que parece un noticiero (CNN, TVN, BBC) pero los titulares son sensacionalistas ("El gobierno oculta esto", "Milagro médico").
   - Si aparecen celebridades, doctores famosos o magnates (Elon Musk, Presidentes) recomendando inversiones o remedios caseros.
   - Si detectas "Lip-sync" extraño o caras muy suavizadas en la imagen.

2. 💊 ALERTA DE "REMEDIOS MÁGICOS" (RIESGO ALTO):
   - Promesas de "curar" diabetes, hipertensión, artrosis o cáncer en pocos días.
   - Frases como "Los médicos te odiarán por este truco", "Remedio natural secreto", "Desaparece el dolor hoy".
   - Venta de polvos, gotas o frascos sin etiqueta oficial clara.

3. 💰 ESTAFAS FINANCIERAS (RIESGO ALTO):
   - Urgencia, bonos del gobierno falsos, "hijo en apuros".

4. ✅ CONTEXTO SEGURO (RIESGO BAJO):
   - Conversaciones familiares normales sobre dinero ("préstame para el uber").
   - Noticias reales sin enlaces de venta.
   - Recetas de cocina o remedios caseros inofensivos (té con miel) sin promesas milagrosas.

Tu tono debe ser protector pero firme. Si detectas un remedio falso, advierte que puede ser peligroso para la salud.
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
