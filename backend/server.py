# server.py

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome to the Dakboard Clone API'})

if __name__ == '__main__':
    app.run(debug=True)