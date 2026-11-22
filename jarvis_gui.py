
import tkinter as tk
from tkinter import scrolledtext
import urllib.request
import json
import threading
import sys

sys.path.insert(0, r"C:\AI-Assistent\geheugen")
import geheugen

MODEL = "qwen3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"


class JarvisApp:

    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS - Personal AI")
        self.root.geometry("950x700")
        self.root.configure(bg="#101820")

        geheugen.initialiseer()

        tk.Label(
            root,
            text="J.A.R.V.I.S.",
            font=("Segoe UI", 26, "bold"),
            fg="#00d9ff",
            bg="#101820"
        ).pack(pady=10)

        self.status = tk.Label(
            root,
            text="● LOKAAL GEHEUGEN ACTIEF",
            fg="#00ff99",
            bg="#101820"
        )
        self.status.pack()

        self.chat = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg="#17232d",
            fg="white",
            insertbackground="white",
            padx=12,
            pady=12
        )
        self.chat.pack(
            padx=20,
            pady=15,
            fill=tk.BOTH,
            expand=True
        )

        frame = tk.Frame(root, bg="#101820")
        frame.pack(fill=tk.X, padx=20, pady=15)

        self.invoer = tk.Entry(
            frame,
            font=("Segoe UI", 12),
            bg="#263746",
            fg="white",
            insertbackground="white"
        )
        self.invoer.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            ipady=10
        )
        self.invoer.bind("<Return>", lambda event: self.verstuur())

        tk.Button(
            frame,
            text="VERSTUUR",
            command=self.verstuur,
            bg="#007f99",
            fg="white",
            padx=20
        ).pack(side=tk.RIGHT, padx=10)

        tk.Button(
            frame,
            text="GEHEUGEN",
            command=self.toon_geheugen,
            bg="#34495e",
            fg="white",
            padx=15
        ).pack(side=tk.RIGHT, padx=5)

        self.chat.insert(
            tk.END,
            "JARVIS: Mijn lokale geheugen is verbonden.\n"
            "JARVIS: Waarmee kan ik je helpen?\n\n"
        )

    def toon_geheugen(self):
        herinneringen = geheugen.toon_alles()
        self.chat.insert(
            tk.END,
            "\nJARVIS GEHEUGEN:\n" + herinneringen + "\n\n"
        )
        self.chat.see(tk.END)

    def verstuur(self):
        tekst = self.invoer.get().strip()

        if not tekst:
            return

        self.invoer.delete(0, tk.END)
        self.chat.insert(tk.END, f"\nJIJ: {tekst}\n")
        self.chat.insert(tk.END, "\nJARVIS: Even nadenken...\n")
        self.chat.see(tk.END)

        threading.Thread(
            target=self.verwerk,
            args=(tekst,),
            daemon=True
        ).start()

    def verwerk(self, tekst):
        try:
            laag = tekst.lower().strip()

            if laag.startswith("onthoud "):
                inhoud = tekst[8:].strip()
                resultaat = geheugen.onthoud("persoonlijk", inhoud)
                antwoord = resultaat

            elif laag in [
                "wat weet je nog?",
                "wat weet je nog",
                "toon mijn geheugen"
            ]:
                antwoord = geheugen.toon_alles()

            else:
                herinneringen = geheugen.zoek(tekst)

                systeemtekst = (
                    "Je bent Jarvis, een persoonlijke "
                    "Nederlandstalige AI-assistent. "
                    "Gebruik relevante informatie uit het "
                    "lokale geheugen. Verzin geen herinneringen.\n\n"
                    "LOKAAL GEHEUGEN:\n" + herinneringen
                )

                gegevens = {
                    "model": MODEL,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": systeemtekst},
                        {"role": "user", "content": tekst}
                    ]
                }

                verzoek = urllib.request.Request(
                    OLLAMA_URL,
                    data=json.dumps(gegevens).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(
                    verzoek, timeout=180
                ) as reactie:
                    resultaat = json.loads(
                        reactie.read().decode("utf-8")
                    )

                antwoord = resultaat["message"]["content"]

        except Exception as fout:
            antwoord = "Er ging iets mis: " + str(fout)

        self.root.after(
            0,
            lambda: self.toon_antwoord(antwoord)
        )

    def toon_antwoord(self, antwoord):
        self.chat.insert(
            tk.END,
            "\nJARVIS: " + antwoord + "\n\n"
        )
        self.chat.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisApp(root)
    root.mainloop()
