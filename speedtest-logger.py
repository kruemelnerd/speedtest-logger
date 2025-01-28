#!/usr/bin/env python3

import csv
import speedtest
from datetime import datetime
import sys

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

def main():
    # Name der CSV-Datei, in der die Ergebnisse gespeichert werden
    filename = "speedtest_results.csv"

    # 1) Speedtest durchführen
    try:
        download, upload, ping = measure_speed()
    except Exception as e:
        # Falls etwas schiefgeht, ggf. in eine Log-Datei schreiben oder ausgeben
        print(f"Fehler bei der Speedtest-Messung: {e}", file=sys.stderr)
        return  # Skript beenden

    # 2) Ergebnis zusammenstellen
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, f"{download:.2f}", f"{upload:.2f}", f"{ping:.2f}"]

    # 3) Ergebnis in CSV-Datei speichern (anfügen)
    try:
        with open(filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Falls die Datei noch leer ist, Header schreiben
            if f.tell() == 0:
                writer.writerow(["timestamp", "download_mbps", "upload_mbps", "ping_ms"])
            writer.writerow(row)
    except Exception as e:
        print(f"Fehler beim Schreiben in die CSV-Datei: {e}", file=sys.stderr)
        return

    # Optionale Ausgabe zur Kontrolle, wird z. B. in Logs geschrieben
    print(f"Speedtest durchgeführt: {row}")

if __name__ == "__main__":
    main()
