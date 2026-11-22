
from pathlib import Path
import shutil

BASIS_MAP = Path(r"C:\AI-Assistent").resolve()


def controleer_pad(pad):
    doel = (BASIS_MAP / pad).resolve()

    if doel != BASIS_MAP and BASIS_MAP not in doel.parents:
        raise ValueError("Toegang buiten de AI-Assistent-map geweigerd.")

    return doel


def zoek_bestanden(zoekterm):
    resultaten = []

    for bestand in BASIS_MAP.rglob("*"):
        if bestand.is_file() and zoekterm.lower() in bestand.name.lower():
            resultaten.append(str(bestand.relative_to(BASIS_MAP)))

    if not resultaten:
        return "Geen bestanden gevonden."

    return "\n".join(resultaten[:50])


def lees_bestand(pad):
    bestand = controleer_pad(pad)

    if not bestand.is_file():
        return "Bestand niet gevonden."

    if bestand.suffix.lower() not in [".txt", ".md", ".py", ".json", ".csv"]:
        return "Dit bestandstype mag voorlopig niet gelezen worden."

    if bestand.stat().st_size > 1_000_000:
        return "Bestand is te groot om te lezen."

    return bestand.read_text(encoding="utf-8")


def maak_map(naam):
    map_pad = controleer_pad(naam)
    map_pad.mkdir(parents=True, exist_ok=True)

    return "Map aangemaakt: " + str(map_pad)


def kopieer_bestand(bron, bestemming):
    bron_pad = controleer_pad(bron)
    bestemming_pad = controleer_pad(bestemming)

    if not bron_pad.is_file():
        return "Bronbestand niet gevonden."

    if bestemming_pad.exists():
        return "Bestemming bestaat al. Er wordt niets overschreven."

    bestemming_pad.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bron_pad, bestemming_pad)

    if not bestemming_pad.is_file():
        return "Kopiëren is niet gelukt."

    return "Bestand succesvol gekopieerd."


if __name__ == "__main__":
    print("Jarvis bestandsbeheer is actief.")
    print("Veilige basismap:", BASIS_MAP)
    print("Beschikbaar: zoeken, lezen, mappen maken en kopiëren.")
