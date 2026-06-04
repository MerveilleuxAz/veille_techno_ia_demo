#!/usr/bin/env python3
"""Exemple d'utilisation du module weather."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from weather import ForecastAPIError, InvalidCoordinatesError, get_forecast, save_forecast


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Récupère la météo Open-Meteo et enregistre le résultat en JSON.",
    )
    parser.add_argument("--lat", type=float, default=48.85, help="Latitude (défaut: Paris)")
    parser.add_argument("--lon", type=float, default=2.35, help="Longitude (défaut: Paris)")
    parser.add_argument(
        "--timezone",
        default="Europe/Paris",
        help="Fuseau horaire IANA (défaut: Europe/Paris)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("forecast.json"),
        help="Fichier JSON de sortie (défaut: forecast.json)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Afficher les logs du module weather",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        forecast = get_forecast(args.lat, args.lon, args.timezone)
    except InvalidCoordinatesError as exc:
        print(f"Coordonnées invalides : {exc}", file=sys.stderr)
        return 1
    except ForecastAPIError as exc:
        print(f"Erreur API : {exc}", file=sys.stderr)
        return 1

    current = forecast["current_weather"]
    hourly = forecast["hourly"]

    print(f"Météo actuelle : {current.get('temperature')} °C")
    print(f"Prochaines {len(hourly['time'])} h (extrait) :")
    for i in range(min(3, len(hourly["time"]))):
        print(
            f"  {hourly['time'][i]}  "
            f"{hourly['temperature_2m'][i]} °C  "
            f"précip. {hourly['precipitation'][i]} mm"
        )

    path = save_forecast(forecast, args.output)
    print(f"\nPrévisions enregistrées dans : {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
