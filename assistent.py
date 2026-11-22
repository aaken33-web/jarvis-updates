
import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

from gereedschap import (
    huidige_tijd,
    lijst_bestanden,
    maak_notitie,
    lees_notitie
)

DB_PATH = Path(r"C:\AI-Assistent\geheugen\geheugen.db")
MODEL = "qwen3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"


# -------------------------
# LOKAAL LANGETERMIJNGEHEUGEN
# -------------------------

def onthoud(categorie, inhoud):
    nu = datetime.now().isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO herinneringen
            (categorie, inhoud, aangemaakt, bijgewerkt)
            VALUES (?, ?, ?, ?)
            """,
            (categorie, inhoud, nu, nu)
        )

    return "Opgeslagen in mijn lokale geheugen: " + inhoud


def haal_herinneringen_op(vraag):
    woorden = [
        woord.strip(".,!?;:()").lower()
        for woord in vraag.split()
        if len(woord.strip(".,!?;:()")) >= 4
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        resultaten = []

        if woorden:
            voorwaarden = " OR ".join(
                ["inhoud LIKE ? OR categorie LIKE ?"] * len(woorden)
            )
            parameters = []

            for woord in woorden:
                parameters.extend([f"%{woord}%", f"%{woord}%"])

            resultaten = conn.execute(
                f"""
                SELECT categorie, inhoud
                FROM herinneringen
                WHERE {voorwaarden}
                ORDER BY bijgewerkt DESC
                LIMIT 10
                """,
                parameters
            ).fetchall()

        if not resultaten:
            resultaten = conn.execute(
                """
                SELECT categorie, inhoud
                FROM herinneringen
                ORDER BY bijgewerkt DESC
                LIMIT 10
                """
            ).fetchall()

    return "\n".join(
        f"- {item['categorie']}: {item['inhoud']}"
        for item in resultaten
    )


# -------------------------
# BESCHIKBARE GEREEDSCHAPPEN
# -------------------------

GEREEDSCHAPPEN = [
    {
        "type": "function",
        "function": {
            "name": "huidige_tijd",
            "description": "Bekijk de huidige datum en tijd.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lijst_bestanden",
            "description": "Bekijk welke bestanden in de Jarvis-documentenmap staan.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maak_notitie",
            "description": "Maak een nieuw tekstbestand in de documentenmap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titel": {
                        "type": "string",
                        "description": "De naam van de notitie."
                    },
                    "inhoud": {
                        "type": "string",
                        "description": "De tekst voor de notitie."
                    }
                },
                "required": ["titel", "inhoud"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lees_notitie",
            "description": "Lees een bestaande notitie uit de documentenmap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titel": {
                        "type": "string",
                        "description": "De naam van de notitie."
                    }
                },
                "required": ["titel"]
            }
        }
    }
]


def voer_gereedschap_uit(naam, argumenten):
    if isinstance(argumenten, str):
        argumenten = json.loads(argumenten)

    if naam == "huidige_tijd":
        return huidige_tijd()

    if naam == "lijst_bestanden":
        return lijst_bestanden()

    if naam == "maak_notitie":
        return maak_notitie(
            argumenten["titel"],
            argumenten["inhoud"]
        )

    if naam == "lees_notitie":
        return lees_notitie(argumenten["titel"])

    return "Dit gereedschap is niet toegestaan."


# -------------------------
# VERBINDING MET QWEN3
# -------------------------

def vraag_ai(vraag):
    herinneringen = haal_herinneringen_op(vraag)

    systeemtekst = (
        "Je bent Jarvis, een persoonlijke Nederlandstalige AI-assistent. "
        "Je kunt beschikbare gereedschappen gebruiken om taken uit te voeren. "
        "Gebruik een gereedschap wanneer dat nodig is. "
        "Vertel eerlijk wat je hebt gedaan en verzin nooit resultaten. "
        "Je mag alleen de aangeboden gereedschappen gebruiken. "
        "Je mag geen bestanden verwijderen of willekeurige opdrachten uitvoeren.\n\n"
        "Lokale herinneringen:\n"
        + (herinneringen if herinneringen else "Geen herinneringen gevonden.")
    )

    berichten = [
        {"role": "system", "content": systeemtekst},
        {"role": "user", "content": vraag}
    ]

    for poging in range(5):
        gegevens = {
            "model": MODEL,
            "stream": False,
            "messages": berichten,
            "tools": GEREEDSCHAPPEN
        }

        verzoek = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(gegevens).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(verzoek, timeout=180) as antwoord:
            resultaat = json.loads(antwoord.read().decode("utf-8"))

        bericht = resultaat["message"]
        berichten.append(bericht)

        tool_calls = bericht.get("tool_calls", [])

        if not tool_calls:
            return bericht.get("content", "Ik heb geen antwoord ontvangen.")

        for oproep in tool_calls:
            functie = oproep["function"]
            naam = functie["name"]
            argumenten = functie.get("arguments", {})

            try:
                uitvoer = voer_gereedschap_uit(naam, argumenten)
            except Exception as fout:
                uitvoer = "Gereedschapsfout: " + str(fout)

            berichten.append({
                "role": "tool",
                "content": str(uitvoer)
            })

    return "Ik heb het maximumaantal gereedschapsstappen bereikt."


# -------------------------
# JARVIS STARTEN
# -------------------------

def start():
    print("====================================")
    print("          JARVIS ASSISTENT")
    print("====================================")
    print("Model:", MODEL)
    print("Geheugen: actief")
    print("Gereedschappen: actief")
    print("Typ 'stop' om af te sluiten.\n")

    while True:
        vraag = input("Jij: ").strip()

        if vraag.lower() in ["stop", "afsluiten", "exit"]:
            print("Jarvis afgesloten.")
            break

        if not vraag:
            continue

        if vraag.lower().startswith("onthoud:"):
            inhoud = vraag[len("onthoud:"):].strip()

            if inhoud:
                print("\nJarvis:", onthoud("persoonlijk", inhoud), "\n")
            else:
                print("\nJarvis: Wat moet ik onthouden?\n")

            continue

        try:
            antwoord = vraag_ai(vraag)
            print("\nJarvis:", antwoord, "\n")

        except urllib.error.URLError:
            print("\nJarvis: Ik kan Ollama niet bereiken. Controleer of Ollama actief is.\n")

        except Exception as fout:
            print("\nJarvis: Er is een fout opgetreden:", fout, "\n")


if __name__ == "__main__":
    start()
