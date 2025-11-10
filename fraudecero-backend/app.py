import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__) # <-- ¡Esta es la línea que faltaba!

# Configura la clave de API desde las Variables de Entorno
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("No se encontró la GEMINI_API_KEY.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error grave al configurar Gemini: {e}")
    model = None

# La instrucción (Prompt) para la IA
SYSTEM_PROMPT = """
Eres "Fraudecero", un asistente de ciberseguridad para proteger a adultos mayores.
Tu misión es analizar un texto y decidir si es un fraude, estafa o phishing.
Sé muy cuidadoso. Si es sospechoso, es mejor prevenir.

Responde ÚNICAMENTE con una de estas tres palabras:
- "rojo": Si es claramente un fraude, phishing o estafa.
- "amarillo": Si es sospechoso, spam o publicidad engañosa.
- "verde": Si estás 99% seguro de que es inofensivo.

Analiza este texto:
"""

@app.route('/check', methods=['POST'])
def check_text():
    if not model:
        return jsonify({"status": "gris", "message": "Error del servidor: El modelo de IA no está disponible."}), 500

    try:
        data = request.json
        text_to_check = data.get('text')

        if not text_to_check or len(text_to_check.strip()) == 0:
            return jsonify({"status": "gris", "message": "No se envió texto."}), 400

        # 1. Llamar a la IA
        full_prompt = SYSTEM_PROMPT + text_to_check
        response = model.generate_content(full_prompt)
        ia_result = response.text.strip().lower()

        # 2. Generar el mensaje simple para el usuario
        status = "gris"
        message = "No pude analizar esto."

        if "rojo" in ia_result:
            status = "rojo"
            message = "¡PELIGRO! Esto parece una estafa. No hagas clic y no respondas."
        elif "amarillo" in ia_result:
            status = "amarillo"
            message = "CUIDADO. Esto es sospechoso. Míralo con calma, probablemente sea publicidad."
        elif "verde" in ia_result:
            status = "verde"
            message = "Parece seguro. Es un mensaje normal."

        # 3. Enviar la respuesta a la app Android
        return jsonify({
            "status": status,
            "message": message
        })

    except Exception as e:
        print(f"Error inesperado en /check: {e}")
        return jsonify({"status": "gris", "message": "Error interno del analizador."}), 500

# Ruta para que Render sepa que la app está viva
@app.route('/')
def health_check():
    return "Fraudecero Backend está vivo!", 200

# Iniciar la app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)