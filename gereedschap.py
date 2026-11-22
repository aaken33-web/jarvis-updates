
from pathlib import Path
from datetime import datetime

# Jarvis mag voorlopig alleen in deze map werken.
DOCUMENTEN_MAP = Path(r"C:\AI-Assistent\documenten")


def controleer_map():
    DOCUMENTEN_MAP.mkdir(parents=True, exist_ok=True)


def huidige_tijd():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def lijst_bestanden():
    controleer_map()

    bestanden = [
        bestand.name
        for bestand in DOCUMENTEN_MAP.iterdir()
        if bestand.is_file()
    ]

    if not bestanden:
        return "Er staan nog geen bestanden in de documentenmap."

    return "\n".join(bestanden)


def maak_notitie(titel, inhoud):
    controleer_map()

    # Alleen eenvoudige bestandsnamen toestaan.
    titel = titel.strip()

    if not titel or Path(titel).name != titel:
        return "Ongeldige titel. Gebruik alleen een bestandsnaam."

    if titel.lower().endswith(".txt"):
        titel = titel[:-4]

    if not titel or titel in [".", ".."]:
        return "Ongeldige titel."

    bestand = DOCUMENTEN_MAP / (titel + ".txt")

    if bestand.exists():
        return "Dit bestand bestaat al. Ik overschrijf het niet."

    bestand.write_text(inhoud, encoding="utf-8")

    return f"Notitie opgeslagen: {bestand.name}"


def lees_notitie(titel):
    controleer_map()

    titel = titel.strip()

    if not titel or Path(titel).name != titel:
        return "Ongeldige bestandsnaam."

    if not titel.lower().endswith(".txt"):
        titel += ".txt"

    bestand = DOCUMENTEN_MAP / titel

    if not bestand.is_file():
        return "Dit bestand bestaat niet."

    return bestand.read_text(encoding="utf-8")


if __name__ == "__main__":
    controleer_map()
    print("Jarvis-gereedschappen zijn klaar.")
    print("Huidige tijd:", huidige_tijd())
    print("Documentenmap:")
    print(DOCUMENTEN_MAP)
