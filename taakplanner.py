
from gereedschap import (
    huidige_tijd,
    lijst_bestanden,
    maak_notitie,
    lees_notitie
)


def voer_stap_uit(stap):
    actie = stap["actie"]
    argumenten = stap.get("argumenten", {})

    if actie == "tijd":
        return huidige_tijd()

    if actie == "bestanden":
        return lijst_bestanden()

    if actie == "notitie_maken":
        return maak_notitie(
            argumenten["titel"],
            argumenten["inhoud"]
        )

    if actie == "notitie_lezen":
        return lees_notitie(argumenten["titel"])

    return "Actie niet toegestaan."


def voer_plan_uit(plan):
    resultaten = []

    for nummer, stap in enumerate(plan, start=1):
        print(f"\nStap {nummer}: {stap['omschrijving']}")

        resultaat = voer_stap_uit(stap)
        resultaten.append(str(resultaat))

        print("Resultaat:", resultaat)

    return resultaten


def test_projectopdracht():
    plan = [
        {
            "omschrijving": "Projectnotitie maken",
            "actie": "notitie_maken",
            "argumenten": {
                "titel": "jarvis_project",
                "inhoud": "Jarvis kan meerdere stappen achter elkaar uitvoeren."
            }
        },
        {
            "omschrijving": "Projectnotitie lezen",
            "actie": "notitie_lezen",
            "argumenten": {
                "titel": "jarvis_project"
            }
        },
        {
            "omschrijving": "Bestanden controleren",
            "actie": "bestanden",
            "argumenten": {}
        }
    ]

    resultaten = voer_plan_uit(plan)

    print("\n========== RAPPORT ==========")

    for nummer, resultaat in enumerate(resultaten, start=1):
        print(f"Stap {nummer}: {resultaat}")

    print("\nTaak afgerond.")


if __name__ == "__main__":
    print("Jarvis taakplanner is actief.")
    test_projectopdracht()
