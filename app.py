from flask import Flask, jsonify

app = Flask(__name__)

app.config.from_object(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'Connect4'}
app.config['SECRET_KEY'] = 'reuvenKing!'
app.config['DEBUG'] = True

from models import db, Board
db.init_app(app)

@app.route("/")
def hello():
    return jsonify(Board.objects.all()), 200

@app.route('/rooms')
def get_rooms():
   pass

if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    app.run('localhost')