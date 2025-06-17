from flaskapi.app import create_app

app = create_app()

@app.route("/")
def home():
    return "Hello from Secure Vault API"

if __name__ == '__main__':
    app.run(debug=True)
