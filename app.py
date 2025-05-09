from flask import Flask, render_template, request, redirect,jsonify
import json
import sqlite3
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS associations (
        id INTEGER PRIMARY KEY,
        player_name TEXT,
        associated_group TEXT,
        notes TEXT
    )''')
    conn.commit()
    conn.close()

##database initialization ^-^
init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/add_association", methods=["GET", "POST"])
def add_association():
    if request.method == "POST":
        player_name = request.form["player_name"]
        associated_group = request.form["associated_group"]
        notes = request.form["notes"]

        conn = sqlite3.connect('players.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO associations (player_name, associated_group, notes) VALUES (?, ?, ?)",
                       (player_name, associated_group, notes))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_association.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_name = request.form["search_name"]
        conn = sqlite3.connect('players.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM associations WHERE player_name LIKE ?", ('%' + search_name + '%',))
        results = cursor.fetchall()
        conn.close()
        return render_template("search_results.html", results=results)
    return render_template("search.html")

@app.route("/profile/<int:player_id>")
def profile(player_id):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM associations WHERE id = ?", (player_id,))
    player = cursor.fetchone()
    conn.close()

    if player:
        player_skin_url = f"https://mc-heads.net/head/{player[1]}"
        return render_template("profile.html", player=player, skin_url=player_skin_url)
    else:
        return "Player not found", 404
        
@app.route("/delete_player/<int:player_id>", methods=["POST"])
def delete_player(player_id):
    conn = sqlite3.connect("players.db")
    c = conn.cursor()

    c.execute("DELETE FROM associations WHERE id = ?", (player_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/search_group", methods=["GET", "POST"])
def search_group():
    if request.method == "POST":
        search_group_name = request.form["search_group"]
        conn = sqlite3.connect('players.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM associations WHERE associated_group LIKE ?", ('%' + search_group_name + '%',))
        results = cursor.fetchall()
        conn.close()

        return render_template("group_search_results.html", results=results, search_group=search_group_name)

    return render_template("search.html")

@app.route("/edit_association/<int:player_id>", methods=["GET", "POST"])
def edit_association(player_id):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM associations WHERE id = ?", (player_id,))
    player = cursor.fetchone()

    if request.method == "POST":
        player_name = request.form["player_name"]
        associated_group = request.form["associated_group"]
        notes = request.form["notes"]

        cursor.execute('''UPDATE associations SET player_name = ?, associated_group = ?, notes = ? WHERE id = ?''',
                       (player_name, associated_group, notes, player_id))
        conn.commit()
        conn.close()

        return redirect(f"/profile/{player_id}")

    conn.close()
    return render_template("edit_association.html", player=player)


##imports ^-^
@app.route('/import', methods=['POST'])
def import_data():
    file = request.files['file']
    data = json.load(file)

    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    for item in data:
        player_name = item['player_name']
        associated_group = item['associated_group']
        notes = item['notes']

        c.execute('SELECT * FROM associations WHERE player_name = ?', (player_name,))
        existing_player = c.fetchone()

        if not existing_player:
            c.execute('''
                INSERT INTO associations (player_name, associated_group, notes)
                VALUES (?, ?, ?)
            ''', (player_name, associated_group, notes))
        else:
            c.execute('''
                UPDATE associations
                SET associated_group = ?, notes = ?
                WHERE player_name = ?
            ''', (associated_group, notes, player_name))

    conn.commit()
    conn.close()

    return 'Data imported successfully', 200


##exports ^-^
@app.route('/export')
def export():
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('SELECT id, player_name, associated_group, notes FROM associations')
    associations_data = c.fetchall()
    conn.close()

    export_data = [
        {"player_name": row[1], "associated_group": row[2], "notes": row[3]}
        for row in associations_data
    ]

    response = app.response_class(
        response=json.dumps(export_data, indent=2),
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = 'attachment; filename=export.json'
    return response

#nuke :(
@app.route('/nukedatabase', methods=['GET', 'POST'])
def nuke_database():
    if request.method == 'POST':
        confirm_text = request.form.get('confirm_text')
        if confirm_text == 'erase':
            db_path = 'players.db'
            if os.path.exists(db_path):
                os.remove(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT,
                    associated_group TEXT,
                    notes TEXT
                )
            ''')
            conn.commit()
            conn.close()

            return render_template('nuked.html')
        else:
            return render_template('nuke_confirm.html', error="Incorrect confirmation text.")

    return render_template('nuke_confirm.html')

if __name__ == "__main__":
    app.run(debug=True)
