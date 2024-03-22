import copy
import csv
import json
import re
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime as dt
from functools import lru_cache
from pprint import pprint

import requests
from sqlmodel import Session, select

from backend.database import engine
from backend.models import Alerts, Stop
from backend.route import app
from util.utils import convert_to_datetime, dateparsing, stopid

service_status = {
    "Delays": "delays.png",
    "Planned - Part Suspended": "suspended.png",
    "Planned - Stations Skipped": "skipped.png",
    "Station Notice": "information.png",
    "Reduced Service": "reduced.png",
}


def process_alert_feed() -> dict:
    """
    Process the alert feed and extract relevant information about subway alerts.

    Returns:
        dict: A dictionary containing information about affected stops and alerts.

         'stop name': { 'line':  str
                        'alertInfo': {'alertType': str,
                                    'createdAt': datetime,
                                    'updatedAt': datetime},
                                    'dates': {'date': [datetime],
                                            'time': [datetime],
                                            'dateText': str },
                                    'direction': str,
                                    'heading': str,
                                    'description': str
                         }



    """

    headers = {"x-api-key": "8ogTVWVBY55OObVPvYpmu4zQAjmlHl3Q8HmQ1BpV"}
    Response = requests.get(
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json",
        headers=headers,
        timeout=10,
    )
    alert_feed = json.loads(Response.content)
    info = defaultdict()
    info = {
        "line": set(),
        "alertInfo": [],
    }
    affected_stops = defaultdict()
    with open("stops.csv", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        affected_stops.update(
            {
                col["stop_id"]: info
                for col in reader
                if col["stop_id"] and col["stop_id"][-1].isdigit()
            }
        )
        affected_stops["None"] = info
    line_stops = defaultdict()
    line_stops = {
        key: copy.deepcopy(value) for key, value in affected_stops.items() if value
    }

    alert_info = []
    for entity in alert_feed["entity"]:

        informed_ent = entity.get("alert", {}).get("informed_entity", {})

        if informed_ent[0].get("route_id", None):

            alert = entity.get("alert", {})
            alert_type = alert.get("transit_realtime.mercury_alert", {})
            translation = alert_type.get("human_readable_active_period", {}).get(
                "translation", {}
            )
            date = (
                translation[0].get("text", {})
                if isinstance(translation, list)
                else translation.get("text", {})
            )
            alert_info = defaultdict()
            alert_info = {
                "alertType": alert_type.get("alert_type", {}),
                "createdAt": alert_type.get("created_at", {}),
                "updatedAt": alert_type.get("updated_at", {}),
                "date": date,
                "direction": None,
                "heading": None,
                "description": None,
            }

            for info in informed_ent:

                head = alert.get("header_text", {}).get("translation", {})
                descr = alert.get("description_text", {}).get("translation", {})

                stop_id = info.get("stop_id", None)
                heading = head[0]["text"]
                direction = re.search(
                    r"(downtown|uptown)|(?!(the|a|an))\b(\w+\s?)(\w*-?)bound",
                    heading,
                )

                alert_info["heading"] = head[0]["text"]
                alert_info["direction"] = direction.group(0) if direction else None
                alert_info["description"] = descr[0]["text"] if descr else ""

                if info.get("stop_id", None) is not None:
                    line_stops[stop_id]["line"].add(informed_ent[0].get("route_id"))
                    line_stops[stop_id]["alertInfo"].append(alert_info)
                else:
                    line_stops["None"]["alertInfo"] = alert_info
                    line_stops["None"]["alertInfo"]["line"] = None
                    line_stops["None"]["alertInfo"]["line"] = informed_ent[0].get(
                        "route_id"
                    )

    return line_stops


def convert_dates(dic):

    for stop in dic.values():
        for alert in stop["alertInfo"]:

            try:

                alert["date"] = dateparsing(alert["date"])
            except AttributeError:
                pass

            alert["createdAt"] = convert_to_datetime(alert["createdAt"])
            alert["updatedAt"] = convert_to_datetime(alert["updatedAt"])
    return dic


def add_alerts_to_db():
    alerts = process_alert_feed()

    with Session(engine) as session:
        for key, values in alerts.items():
            for line in values["line"]:
                stop = Stop(
                    stop=str(key),
                    route=line,
                )
                for alert in values["alertInfo"]:
                    alerts = Alerts(
                        alert_type=alert["alertType"],
                        created_at=alert["createdAt"],
                        updated_at=alert["updatedAt"],
                        direction=alert["direction"],
                        heading=alert["heading"],
                        stops=[stop],
                        dateText=alert.get("alertInfo", {})
                        .get("date", {})
                        .get("dateText", ""),
                    )
                    session.add(alerts)
                    session.commit()
                    session.refresh(alerts)

                session.add(stop)
                session.commit()
                session.refresh(stop)


def select_heroes():
    with Session(engine) as session:
        statement = select(Stop).where(Stop.route == "2")
        result = session.exec(statement)
        alertType = result.all()

        # Code from the previous example omitted 👈

        pprint(
            [
                f"{stopid(x.stop)}___{x.alert.heading}"
                for x in alertType
                if x.alert is not None
            ]
        )


alerts = process_alert_feed()


# converted_alerts = convert_dates(alerts)

pprint(alerts)
