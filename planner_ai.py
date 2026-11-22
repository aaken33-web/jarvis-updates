
import json
import urllib.request
import urllib.error

from gereedschap import (
    huidige_tijd, lijst_bestanden, maak_notitie, lees_notitie
)
from bestandsbeheer import (
    zoek_bestanden, lees_bestand, maak_map, kopieer_bestand
)
from windows_tools import start_programma

MODEL = "qwen3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"


def maak_plan(opdracht):
    systeemtekst = """
Je bent Jarvis, een persoonlijke Nederlandse AI-agent.

Maak een stappenplan in JSON.

Toegestane acties:

tijd: {}
bestanden: {}
notitie_maken: {"titel":"naam","inhoud":"tekst"}
notitie_lezen: {"titel":"naam"}
zoeken: {"zoekterm":"naam"}
bestand_lezen: {"pad":"bestand.txt"}
map_maken: {"naam":"map"}
bestand_kopieren: {"bron":"bestand.txt","bestemming":"kopie.txt"}
programma_starten: {"naam":"kladblok"}

Toegestane programma's:
kladblok, rekenmachine, verkenner, paint.

Regels:
- Maximaal 5 stappen.
- Gebruik uitsluitend bovenstaande acties.
- Geef uitsluitend geldige JSON terug.
- Gebruik geen andere Windows-programma's.

Structuur:
{
 "plan": [
  {
   "omschrijving": "Beschrijving",
   "actie": "tijd",
   "argumenten": {}
  }
 ]
}
"""

    gegevens = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": systeemtekst},
            {"role": "user", "content": opdracht}
        ]
    }

    verzoek = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(gegevens).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(verzoek, timeout=180) as antwoord:
        resultaat = json.loads(antwoord.read().decode("utf-8"))

    return json.loads(resultaat["message"]["content"])


def controleer_plan(plan):
    toegestaan = {
        "tijd": set(),
        "bestanden": set(),
        "notitie_maken": {"titel", "inhoud"},
        "notitie_lezen": {"titel"},
        "zoeken": {"zoekterm"},
        "bestand_lezen": {"pad"},
        "map_maken": {"naam"},
        "bestand_kopieren": {"bron", "bestemming"},
        "programma_starten": {"naam"}
    }

    if not isinstance(plan, list) or not 1 <= len(plan) <= 5:
        raise ValueError("Plan moet 1 tot 5 stappen bevatten.")

    for stap in plan:
        if not isinstance(stap, dict):
            raise ValueError("Ongeldige stap.")

        actie = stap.get("actie")
        argumenten = stap.get("argumenten", {})

        if actie not in toegestaan:
            raise ValueError("Actie niet toegestaan.")

        if not isinstance(argumenten, dict):
            raise ValueError("Ongeldige argumenten.")

        if set(argumenten) != toegestaan[actie]:
            raise ValueError("Ongeldige argumenten voor actie.")

        if not all(isinstance(v, str) for v in argumenten.values()):
            raise ValueError("Argumenten moeten tekst zijn.")

        if actie == "programma_starten":
            if argumenten["naam"].lower() not in {
                "kladblok", "rekenmachine", "verkenner", "paint"
            }:
                raise ValueError("Programma niet toegestaan.")


def voer_actie_uit(stap):
    actie = stap["actie"]
    a = stap.get("argumenten", {})

    functies = {
        "tijd": lambda: huidige_tijd(),
        "bestanden": lambda: lijst_bestanden(),
        "notitie_maken": lambda: maak_notitie(a["titel"], a["inhoud"]),
        "notitie_lezen": lambda: lees_notitie(a["titel"]),
        "zoeken": lambda: zoek_bestanden(a["zoekterm"]),
        "bestand_lezen": lambda: lees_bestand(a["pad"]),
        "map_maken": lambda: maak_map(a["naam"]),
        "bestand_kopieren": lambda: kopieer_bestand(a["bron"], a["bestemming"]),
        "programma_starten": lambda: start_programma(a["naam"])
    }

    if actie not in functies:
        raise ValueError("Actie niet toegestaan.")

    return functies[actie]()


def start():
    print("================================")
    print("       JARVIS WINDOWS AI")
    print("================================")
    print("Windows-bediening actief.")
    print("Typ stop om af te sluiten.\n")

    while True:
        opdracht = input("Jij: ").strip()

        if opdracht.lower() in ["stop", "exit", "afsluiten"]:
            print("Jarvis afgesloten.")
            break

        if not opdracht:
            continue

        try:
            gegevens = maak_plan(opdracht)
            plan = gegevens["plan"]
            controleer_plan(plan)

            print("\nJARVIS TAAKPLAN:")

            for nummer, stap in enumerate(plan, 1):
                print(f"{nummer}. {stap['omschrijving']}")
                print("   Actie:", stap["actie"])

            toestemming = input(
                "\nMag Jarvis dit uitvoeren? (ja/nee): "
            ).strip().lower()

            if toestemming != "ja":
                print("Uitvoering geannuleerd.")
                continue

            for nummer, stap in enumerate(plan, 1):
                print(f"\nStap {nummer}: {stap['omschrijving']}")

                try:
                    resultaat = voer_actie_uit(stap)
                    print("Resultaat:", resultaat)
                except Exception as fout:
                    print("FOUT:", fout)

            print("\nJarvis heeft het plan verwerkt.")

        except urllib.error.URLError:
            print("Ollama is niet bereikbaar.")
        except Exception as fout:
            print("Fout:", fout)


if __name__ == "__main__":
    start()
