
import subprocess

PROGRAMMA_S = {
    "kladblok": ["notepad.exe"],
    "rekenmachine": ["calc.exe"],
    "verkenner": ["explorer.exe"],
    "paint": ["mspaint.exe"]
}


def start_programma(naam):
    naam = naam.lower().strip()

    if naam not in PROGRAMMA_S:
        return "Dit programma staat niet op de toegestane lijst."

    subprocess.Popen(PROGRAMMA_S[naam])

    return f"{naam.capitalize()} is gestart."


if __name__ == "__main__":
    print("Jarvis Windows-bediening actief.")

    for naam in PROGRAMMA_S:
        print("-", naam)
