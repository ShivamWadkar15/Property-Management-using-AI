# app.py
# --- IMPORTS ---
from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from mysql.connector import Error
import json
import os
import google.generativeai as genai # Using the official Python SDK

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'shivam',  # IMPORTANT: Enter your MySQL password here
    'database': 'property_db'
}

# --- GEMINI API CONFIGURATION ---
# The API key you provided
API_KEY = "AIzaSyBaczF7Z18gzWXddh9NicOtmfln8oEA2A8"

# Configure the generative AI client using the SDK
try:
    genai.configure(api_key=API_KEY)
    # Using the stable 'gemini-2.5-flash' model which is best for this text-based task
    model = genai.GenerativeModel("gemini-2.5-flash")
    print("AI DEBUG: Gemini AI model ('gemini-2.5-flash') initialized successfully.")
except Exception as e:
    print(f"AI CONFIGURATION ERROR: {e}")
    model = None

# --- HELPER FUNCTIONS ---
def create_connection():
    """Creates a reusable database connection."""
    try:
        return mysql.connector.connect(**db_config)
    except Error as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None

def get_compliance_from_ai(address):
    """
    Calls Gemini API using the Python SDK to get a compliance checklist.
    """
    if not model:
        print("AI DEBUG: Model not initialized. Skipping AI feature.")
        return []

    print(f"AI DEBUG: Calling Gemini API for address: {address[:40]}...")
    prompt = f"""
    Analyze the property address: "{address}".
    Based on its state/city in India, generate a JSON array of the top 5 rental compliance tasks.
    The output must be a valid JSON array of objects. Each object must have "category" and "rule" keys.
    IMPORTANT: The "rule" description must be a very brief, actionable point, under 10 words.

    Example for Mumbai:
    [
        {{"category": "Verification", "rule": "Submit tenant police verification online."}},
        {{"category": "Agreement", "rule": "Register leave and license agreement."}},
        {{"category": "Society", "rule": "Obtain society NOC for the tenant."}}
    ]
    """
    
    try:
        # Configuration to ask the model to return a JSON object
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        print("AI DEBUG: API response received successfully.")
        
        # The response text itself is the JSON string
        json_string = response.text
        
        print("AI DEBUG: Parsing JSON from AI response.")
        compliance_list = json.loads(json_string)
        print(f"AI DEBUG: JSON parsed successfully, found {len(compliance_list)} rules.")
        return compliance_list

    except Exception as e:
        print(f"An unexpected error occurred in get_compliance_from_ai: {e}")
        return []

# --- ROUTES ---
@app.route('/')
def dashboard():
    """Main dashboard to view all properties and their compliance checklists."""
    connection = create_connection()
    if not connection:
        return "Error: Could not connect to the database. Please check server status and app.py config.", 500

    properties = []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Property ORDER BY id DESC")
        properties = cursor.fetchall()

        for prop in properties:
            cursor.execute("SELECT * FROM PropertyCompliance WHERE property_id = %s", (prop['id'],))
            compliance_tasks = cursor.fetchall()

            if not compliance_tasks:
                print(f"DEBUG: No compliance tasks in DB for property {prop['id']}. Calling AI.")
                ai_rules = get_compliance_from_ai(prop['address'])
                if ai_rules:
                    new_tasks = []
                    for rule_item in ai_rules:
                        if isinstance(rule_item, dict) and 'rule' in rule_item:
                            cursor.execute(
                                "INSERT INTO PropertyCompliance (property_id, rule_description, is_completed) VALUES (%s, %s, %s)",
                                (prop['id'], rule_item['rule'], False)
                            )
                            # We need the ID of the newly inserted row for the frontend
                            task_id = cursor.lastrowid
                            new_tasks.append({'id': task_id, 'rule_description': rule_item['rule'], 'is_completed': False})
                    connection.commit()
                    prop['compliance'] = new_tasks
                    print(f"DEBUG: Stored {len(new_tasks)} new tasks for property {prop['id']}.")
                else:
                    prop['compliance'] = []
            else:
                print(f"DEBUG: Found {len(compliance_tasks)} tasks in DB for property {prop['id']}.")
                prop['compliance'] = compliance_tasks

    except Error as e:
        print(f"Dashboard loading error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    return render_template('dashboard.html', properties=properties)


@app.route('/add', methods=['GET', 'POST'])
def add_property():
    """Handles adding a new property."""
    if request.method == 'POST':
        connection = create_connection()
        if not connection: return "Database connection error.", 500
        
        try:
            cursor = connection.cursor()
            query = "INSERT INTO Property (address, type, monthly_rent, status) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (
                request.form['address'],
                request.form['type'],
                request.form['monthly_rent'],
                request.form['status']
            ))
            connection.commit()
        except Error as e:
            print(f"Error adding property: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
        return redirect(url_for('dashboard'))
    
    return render_template('add_property.html')


@app.route('/edit/<int:id>', methods=['POST'])
def edit_property(id):
    """Handles inline editing of a property from the dashboard."""
    connection = create_connection()
    if not connection: return jsonify({'success': False, 'message': 'Database connection error'}), 500

    try:
        data = request.get_json()
        cursor = connection.cursor()
        query = "UPDATE Property SET address=%s, type=%s, monthly_rent=%s, status=%s WHERE id=%s"
        cursor.execute(query, (data['address'], data['type'], data['monthly_rent'], data['status'], id))
        connection.commit()
        return jsonify({'success': True})
    except Error as e:
        print(f"Error updating property {id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/delete/<int:id>', methods=['POST'])
def delete_property(id):
    """Handles deleting a property."""
    connection = create_connection()
    if not connection: return "Database connection error.", 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Property WHERE id = %s", (id,))
        connection.commit()
    except Error as e:
        print(f"Error deleting property {id}: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return redirect(url_for('dashboard'))


@app.route('/compliance/toggle', methods=['POST'])
def toggle_compliance():
    """Toggles the completion state of a compliance task."""
    connection = create_connection()
    if not connection: return jsonify({'success': False, 'message': 'Database connection error'}), 500

    try:
        data = request.get_json()
        task_id = data['task_id']
        
        cursor = connection.cursor()
        cursor.execute("SELECT is_completed FROM PropertyCompliance WHERE id = %s", (task_id,))
        result = cursor.fetchone()

        if result:
            new_status = not result[0]
            cursor.execute("UPDATE PropertyCompliance SET is_completed = %s WHERE id = %s", (new_status, task_id))
            connection.commit()
            return jsonify({'success': True, 'is_completed': new_status})
        else:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
            
    except Error as e:
        print(f"Error toggling compliance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)
