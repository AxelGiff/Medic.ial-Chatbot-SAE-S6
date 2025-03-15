import json
import psycopg2
from psycopg2 import OperationalError
import os

def handler(event, context):
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            sslmode='require'
        )
        cur = conn.cursor()
        cur.execute('SELECT * FROM users;')
        users = cur.fetchall()
        cur.close()
        conn.close()
        return {
            'statusCode': 200,
            'body': json.dumps(users)
        }
    except OperationalError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }