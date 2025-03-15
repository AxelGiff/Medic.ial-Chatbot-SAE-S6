from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import OperationalError
import logging
import os

app = Flask(__name__)
CORS(app)  # Ajout de CORS

# Configurer la journalisation
logging.basicConfig(level=logging.DEBUG)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT'),
        sslmode='require'
    )
    return conn

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (name, email) VALUES (%s, %s);
        ''', (name, email))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "User inserted successfully"}), 201
    except OperationalError as e:
        logging.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users;')
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(users), 200
    except OperationalError as e:
        logging.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)