from flask import Flask
from config import Config
from app.extensions import db, migrate, limiter, cache

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)
cache.init_app(app)

@app.route("/")
def home():
    return "🔧 Mechanic Shop API is alive!"

if __name__ == "__main__":
    app.run(debug=True)
