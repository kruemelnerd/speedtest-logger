#!/usr/bin/env python3

import csv
import speedtest
import os
from datetime import datetime, timezone
import sys

from dotenv import load_dotenv


# InfluxDB-Client (für InfluxDB 2.x)
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


load_dotenv()  # Sucht nach .env im aktuellen Verzeichnis und lädt die Variablen

# -----------------------------------------------------------------------------
# Globale Variablen für CSV und InfluxDB
# -----------------------------------------------------------------------------

CSV_FILENAME = os.getenv("CSV_FILENAME", "speedtest_results.csv")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "myOrg")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "myBucket")


def measure_speed():
    """
    Führt einen Speedtest durch und gibt Download-, Upload-Geschwindigkeit
    (in MBit/s) und Ping (in ms) zurück.
    """
    s = speedtest.Speedtest()
    s.get_best_server()

    download_speed = s.download() / 1_000_000  # MBit/s
    upload_speed = s.upload() / 1_000_000      # MBit/s
    ping_ms = s.results.ping                   # ms

    return download_speed, upload_speed, ping_ms

def write_to_csv(timestamp, download, upload, ping):
    """
    Schreibt die Messergebnisse in eine CSV-Datei (Anhängen einer Zeile).
    Legt die Datei an, falls sie noch nicht existiert.
    """
    try:
        with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Falls die Datei leer ist, Kopfzeile schreiben
            if f.tell() == 0:
                writer.writerow(["timestamp", "download_mbps", "upload_mbps", "ping_ms"])
            writer.writerow([timestamp, f"{download:.2f}", f"{upload:.2f}", f"{ping:.2f}"])
    except Exception as e:
        print(f"[CSV] Fehler beim Schreiben in die CSV-Datei: {e}", file=sys.stderr)


def write_to_influx(timestamp, download, upload, ping):
    """
    Schreibt die Messergebnisse in eine InfluxDB (v2.x).
    """
    try:
        # InfluxDB-Client initialisieren
        with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)


            # Messpunkt vorbereiten (Measurement: "internet_speed")
            point = (
                Point("internet_speed")
                .tag("source", "speedtest_cron")  # Beispiel-Tag
                .field("download_mbps", float(download))
                .field("upload_mbps", float(upload))
                .field("ping_ms", float(ping))
                # Zeitstempel in UTC (WritePrecision.S = Sekundenauflösung)
                .time(datetime.now(timezone.utc), WritePrecision.S)
            )

            # InfluxDB schreiben
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

    except Exception as e:
        print(f"[InfluxDB] Fehler beim Schreiben in die InfluxDB: {e}", file=sys.stderr)


def main():

    # 1) Speedtest durchführen
    try:
        download, upload, ping = measure_speed()
    except Exception as e:
        # Falls etwas schiefgeht, ggf. in eine Log-Datei schreiben oder ausgeben
        print(f"Fehler bei der Speedtest-Messung: {e}", file=sys.stderr)
        return  # Skript beenden

    # 2) Ergebnis zusammenstellen
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Optionale Ausgabe zur Kontrolle, wird z. B. in Logs geschrieben
    row = [timestamp, f"{download:.2f}", f"{upload:.2f}", f"{ping:.2f}"]
    print(f"Speedtest durchgeführt: {row}")

    # 3) Ergebnis in CSV-Datei speichern (anfügen)
    write_to_csv(timestamp, download, upload, ping)
    print(" and written into a file")

    # 4) In InfluxDB schreiben
    write_to_influx(timestamp, download, upload, ping)
    print(" and written into a database.")


if __name__ == "__main__":
    main()
