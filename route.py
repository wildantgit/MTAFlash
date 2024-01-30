from flask import Flask, render_template

import alertfeedStatic as af

app = Flask(__name__)


@app.route("/")
def hello():
    return render_template(
        "home.html", affectedStations=af.affectedStops, serviceStatus=af.ServiceStatus
    )


if __name__ == "__main__":
    app.run(debug=True)
