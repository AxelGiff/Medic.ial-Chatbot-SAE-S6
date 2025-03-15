import json
import psycopg2
from psycopg2 import OperationalError
import os

def handler(event, context):
    data = json.loads(event['body'])
    name = data.get('name')
    email = data.get('email')

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
        cur.execute('''
            INSERT INTO users (name, email) VALUES (%s, %s);
        ''', (name, email))
        conn.commit()
        cur.close()
        conn.close()
        return {
            'statusCode': 201,
            'body': json.dumps({"message": "User inserted successfully"})
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