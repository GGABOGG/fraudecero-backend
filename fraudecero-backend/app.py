import os
from flask import Flask, request, jsonify
from openai import OpenAI
import json

app = Flask(__name__)

# --- Configuración de OpenAI ---
client = None
try:
    # Intenta obtener la clave de la variable de entorno
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        # Esto lanzará un error para que la ruta /check sepa que debe fallar.
        raise ValueError("No se encontró la OPENAI_API_KEY en el entorno.")
    
    # Inicializa el cliente de OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"Error grave al configurar OpenAI: {e}")
    client = None

# EL PROMPT: La instrucción para la IA
SYSTEM_PROMPT = """
Eres "Fraudecero", un asistente de ciberseguridad diseñado para proteger a adultos mayores.
Tu misión es analizar el siguiente texto y determinar si es un fraude, una estafa o phishing.
Sé muy cuidadoso. Si algo es remotamente sospechoso, es mejor prevenir.

Responde ÚNICAMENTE con una de estas tres palabras: "rojo", "amarillo", o "verde".
"""

@app.route('/check', methods=['POST'])
def check_text():
    # 1. Comprueba si el cliente de OpenAI se inicializó correctamente
    if not client:
        return jsonify({"status": "gris", "message": "Error del servidor: La clave de OpenAI no está configurada."}), 500
    
    # 2. Obtiene el texto del cuerpo JSON de la solicitud
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"status": "gris", "message": "Error: Se espera un JSON con la clave 'text'."}), 400
        
        text_to_check = data.get('text', '')
        if not text_to_check:
             return jsonify({"status": "gris", "message": "Error: El campo 'text' no puede estar vacío."}), 400

    except Exception as e:
        return jsonify({"status": "gris", "message": f"Error al analizar el JSON: {e}"}), 400
    
    # 3. Llama a la IA de OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Modelo estable y rápido
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text_to_check}
            ],
            max_tokens=5, # Solo necesitamos 'rojo', 'amarillo', o 'verde'
            temperature=0.0 # Pide una respuesta determinista
        )
        
        # Extrae y limpia el resultado
        ia_result = response.choices[0].message.content.strip().lower()

        # 4. Generar la respuesta final (El código del semáforo)
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

        return jsonify({"status": status, "message": message})

    except Exception as e:
        print(f"Error en /check al llamar a la IA: {e}")
        # Si la clave es inválida, este error es lo que el servidor devuelve.
        if "api_key not valid" in str(e).lower() or "authentication" in str(e).lower():
             return jsonify({"status": "gris", "message": "Error del servidor: La clave de OpenAI es inválida."}), 500
        return jsonify({"status": "gris", "message": "Error interno del analizador."}), 500

if __name__ == '__main__':
    # Usamos Gunicorn en Render, pero esto es útil para probar localmente
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)