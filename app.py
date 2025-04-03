from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "El servicio está funcionando correctamente con hot reload activado"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 