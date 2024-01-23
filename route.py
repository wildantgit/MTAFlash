from flask import Flask, render_template

import alertfeedStatic as af

app = Flask(__name__)


@app.route("/")
def hello():
    return render_template("home.html", info=af.final)


if __name__ == "__main__":
    app.run(debug=True)
