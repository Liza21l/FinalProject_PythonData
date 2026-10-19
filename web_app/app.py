
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>Banking Fintech Platform</h1>
    <p>Our banking platform is starting!</p>
    """


if __name__ == "__main__":
    app.run(debug=True)
