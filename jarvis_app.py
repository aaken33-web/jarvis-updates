import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3, json, threading, urllib.request, urllib.error, subprocess, os, re
from pathlib import Path
from datetime import datetime

ROOT=Path(r"C:\AI-Assistent"); DB=ROOT/"geheugen"/"geheugen.db"
MODEL="qwen3:4b"; API="http://127.0.0.1:11434/api/chat"; TAGS="http://127.0.0.1:11434/api/tags"
BG="#0a1220"; PANEL="#111d30"; PANEL2="#192840"; CYAN="#36d5e5"; WHITE="#edf5ff"; MUTED="#91a4bd"; GREEN="#54d6a0"

class Jarvis:
 def __init__(self,root):
  self.root=root; root.title("JARVIS 3.0 | Personal AI"); root.geometry("1240x800"); root.minsize(980,650); root.configure(bg=BG)
  self.busy=False; self.history=[]; self.pending_memory=None
  self.initdb(); self.style(); self.shell(); self.chat_page(); self.status_check()
 def con(self): return sqlite3.connect(DB)
 def initdb(self):
  DB.parent.mkdir(parents=True,exist_ok=True)
  with self.con() as c:
   c.execute("CREATE TABLE IF NOT EXISTS herinneringen(id INTEGER PRIMARY KEY AUTOINCREMENT,categorie TEXT NOT NULL,inhoud TEXT NOT NULL,aangemaakt TEXT NOT NULL,bijgewerkt TEXT NOT NULL)")
   c.execute("CREATE TABLE IF NOT EXISTS gesprekken(id INTEGER PRIMARY KEY AUTOINCREMENT,rol TEXT NOT NULL,inhoud TEXT NOT NULL,tijd TEXT NOT NULL)")
   c.execute("CREATE TABLE IF NOT EXISTS taken(id INTEGER PRIMARY KEY AUTOINCREMENT,titel TEXT NOT NULL,details TEXT DEFAULT '',status TEXT NOT NULL DEFAULT 'Open',aangemaakt TEXT NOT NULL)")
 def style(self):
  s=ttk.Style(); s.theme_use("clam"); s.configure("Treeview",background=PANEL2,foreground=WHITE,fieldbackground=PANEL2,rowheight=30)
  s.configure("Treeview.Heading",background=PANEL,foreground=CYAN,font=("Segoe UI",10,"bold"))
 def shell(self):
  top=tk.Frame(self.root,bg=BG); top.pack(fill="x",padx=22,pady=15)
  tk.Label(top,text="J.A.R.V.I.S.",bg=BG,fg=CYAN,font=("Segoe UI",25,"bold")).pack(side="left")
  tk.Label(top,text="PERSONAL AI  /  LOCAL MODE",bg=BG,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=16,pady=12)
  self.status=tk.Label(top,text="● CONTROLEREN",bg=BG,fg=MUTED,font=("Segoe UI",10,"bold")); self.status.pack(side="right")
  body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True,padx=18,pady=(0,18))
  nav=tk.Frame(body,bg=PANEL,width=215); nav.pack(side="left",fill="y",padx=(0,14)); nav.pack_propagate(False)
  tk.Label(nav,text="WERKRUIMTE",bg=PANEL,fg=MUTED,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=16,pady=18)
  for t,f in [("◈  Chat",self.chat_page),("▤  Geheugen",self.memory_page),("✓  Taken & agent",self.agent_page),("🎙  Spraak",self.voice_page),("⚙  Instellingen",self.settings_page)]:
   tk.Button(nav,text=t,command=f,bg=PANEL,fg=WHITE,activebackground=PANEL2,activeforeground=CYAN,relief="flat",anchor="w",font=("Segoe UI",11),padx=16,pady=12).pack(fill="x",padx=7)
  tk.Frame(nav,bg="#293950",height=1).pack(fill="x",padx=15,pady=16)
  tk.Label(nav,text="AI-MODEL",bg=PANEL,fg=MUTED,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=16)
  tk.Label(nav,text=MODEL,bg=PANEL,fg=WHITE,font=("Segoe UI",11,"bold")).pack(anchor="w",padx=16,pady=5)
  tk.Label(nav,text="Ollama • SQLite • offline",bg=PANEL,fg=GREEN,font=("Segoe UI",9)).pack(anchor="w",padx=16)
  self.main=tk.Frame(body,bg=BG); self.main.pack(side="left",fill="both",expand=True)
 def clear(self):
  for w in self.main.winfo_children(): w.destroy()
 def head(self,a,b):
  tk.Label(self.main,text=a,bg=BG,fg=WHITE,font=("Segoe UI",21,"bold")).pack(anchor="w",pady=(4,2))
  tk.Label(self.main,text=b,bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w",pady=(0,13))
 def say(self,who,msg):
  if not hasattr(self,"transcript") or not self.transcript.winfo_exists(): return
  self.transcript.configure(state="normal"); self.transcript.insert("end",who+"\n","who"); self.transcript.insert("end",msg+"\n\n")
  self.transcript.see("end"); self.transcript.configure(state="disabled")
 def chat_page(self):
  self.clear(); self.head("Chat met Jarvis","Lokale gesprekken, context en geheugen.")
  self.transcript=tk.Text(self.main,bg=PANEL,fg=WHITE,insertbackground=WHITE,font=("Segoe UI",11),wrap="word",relief="flat",padx=16,pady=14)
  self.transcript.pack(fill="both",expand=True); self.transcript.tag_configure("who",foreground=CYAN,font=("Segoe UI",10,"bold")); self.transcript.configure(state="disabled")
  row=tk.Frame(self.main,bg=BG); row.pack(fill="x",pady=(10,0))
  self.entry=tk.Entry(row,bg=PANEL2,fg=WHITE,insertbackground=WHITE,relief="flat",font=("Segoe UI",12)); self.entry.pack(side="left",fill="x",expand=True,ipady=13,padx=(0,9)); self.entry.bind("<Return>",lambda e:self.send())
  self.sendbtn=tk.Button(row,text="VERSTUUR ➤",command=self.send,bg="#087f91",fg="white",relief="flat",padx=20,pady=12); self.sendbtn.pack(side="right")
  self.say("JARVIS","Jarvis 3.0 is gereed. Belangrijke persoonlijke informatie kan ik herkennen en ter goedkeuring aanbieden.")
 def ask(self,payload,timeout=240):
  req=urllib.request.Request(API,data=json.dumps(payload,ensure_ascii=False).encode(),headers={"Content-Type":"application/json"})
  with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())["message"]["content"]
 def send(self):
  if self.busy:return
  p=self.entry.get().strip()
  if not p:return
  self.entry.delete(0,"end"); self.say("JIJ",p); self.busy=True; self.sendbtn.config(state="disabled",text="BEZIG...")
  threading.Thread(target=self.answer,args=(p,),daemon=True).start()
 def answer(self,p):
  try:
   lo=p.lower().strip()
   if lo.startswith("onthoud "):
    self.save("persoonlijk",p[8:].strip()); a="Opgeslagen in mijn lokale geheugen."
   elif lo in ("wat weet je nog","wat weet je nog?","toon mijn geheugen"):
    a=self.memtext()
   elif lo.startswith("taak:"):
    self.task(p[5:].strip()); a="Taak toegevoegd aan je takenlijst."
   else:
    context=self.search(p)
    system=("Je bent Jarvis, een behulpzame Nederlandstalige persoonlijke assistent. Je draait lokaal. "
    "Gebruik alleen relevante herinneringen. Je kunt voorstellen doen, maar voer geen niet-goedgekeurde systeemacties uit. "
    "Als iets belangrijk en langdurig persoonlijks lijkt, vermeld aan het eind exact één korte regel: "
    "[GEHEUGENVOORSTEL: categorie | inhoud]. Doe dit alleen voor duidelijke duurzame feiten of voorkeuren, niet voor losse vragen, gevoelige medische, politieke, religieuze of andere gevoelige gegevens. "
    "Verzin geen gegevens.\n\nLOKAAL GEHEUGEN:\n"+context)
    messages=[{"role":"system","content":system}]+self.history[-8:]+[{"role":"user","content":p}]
    a=self.ask({"model":MODEL,"stream":False,"messages":messages})
    self.history.extend([{"role":"user","content":p},{"role":"assistant","content":a}])
    m=re.search(r"\[GEHEUGENVOORSTEL:\s*([^|]+)\|\s*(.*?)\]",a,re.I|re.S)
    if m:
     cat,val=m.group(1).strip(),m.group(2).strip(); a=re.sub(r"\[GEHEUGENVOORSTEL:.*?\]","",a,flags=re.I|re.S).strip()
     self.root.after(0,lambda:self.propose_memory(cat,val))
   self.log("user",p); self.log("assistant",a)
  except urllib.error.URLError:a="Ollama niet bereikbaar. Controleer of Ollama actief is."
  except Exception as e:a="Fout: "+str(e)
  self.root.after(0,self.finish,a)
 def finish(self,a):
  self.say("JARVIS",a); self.busy=False
  if hasattr(self,"sendbtn") and self.sendbtn.winfo_exists():self.sendbtn.config(state="normal",text="VERSTUUR ➤")
 def propose_memory(self,cat,val):
  if messagebox.askyesno("Geheugenvoorstel","Wil je dit lokaal onthouden?\n\nCategorie: "+cat+"\n\n"+val):
   self.save(cat,val); messagebox.showinfo("Jarvis","Opgeslagen in je lokale geheugen.")
 def save(self,cat,val):
  now=datetime.now().isoformat(timespec="seconds")
  with self.con() as c:c.execute("INSERT INTO herinneringen(categorie,inhoud,aangemaakt,bijgewerkt) VALUES(?,?,?,?)",(cat,val,now,now))
 def memtext(self):
  with self.con() as c:r=c.execute("SELECT id,categorie,inhoud FROM herinneringen ORDER BY id").fetchall()
  return "\n".join(f"[{i}] {cat}: {v}" for i,cat,v in r) or "Nog geen herinneringen."
 def search(self,p):
  words=[x for x in p.split() if len(x)>3][:6]
  if not words:return "Geen passende herinneringen."
  clause=" OR ".join("inhoud LIKE ?" for _ in words)
  with self.con() as c:r=c.execute(f"SELECT categorie,inhoud FROM herinneringen WHERE {clause} ORDER BY bijgewerkt DESC LIMIT 10",tuple("%"+x+"%" for x in words)).fetchall()
  return "\n".join(f"{x}: {y}" for x,y in r) or "Geen passende herinneringen."
 def log(self,role,val):
  with self.con() as c:c.execute("INSERT INTO gesprekken(rol,inhoud,tijd) VALUES(?,?,?)",(role,val,datetime.now().isoformat(timespec="seconds")))
 def memory_page(self):
  self.clear(); self.head("Lokaal geheugen","Jij beslist wat Jarvis bewaart.")
  bar=tk.Frame(self.main,bg=BG);bar.pack(fill="x",pady=(0,9))
  tk.Button(bar,text="+ Toevoegen",command=self.add_memory,bg="#087f91",fg="white",relief="flat",padx=14,pady=9).pack(side="left")
  tk.Button(bar,text="Verwijderen",command=self.del_memory,bg="#63313d",fg="white",relief="flat",padx=14,pady=9).pack(side="left",padx=8)
  self.mt=ttk.Treeview(self.main,columns=("cat","val"),show="headings");self.mt.heading("cat",text="CATEGORIE");self.mt.heading("val",text="HERINNERING");self.mt.column("cat",width=150,stretch=False);self.mt.pack(fill="both",expand=True)
  with self.con() as c: rows=c.execute("SELECT id,categorie,inhoud FROM herinneringen ORDER BY id DESC").fetchall()
  for i,x,y in rows:self.mt.insert("","end",iid=str(i),values=(x,y))
 def add_memory(self):
  v=simpledialog.askstring("Herinnering","Wat moet Jarvis onthouden?",parent=self.root)
  if v:
   c=simpledialog.askstring("Categorie","Categorie:",initialvalue="persoonlijk",parent=self.root) or "persoonlijk";self.save(c,v);self.memory_page()
 def del_memory(self):
  ids=self.mt.selection()
  if ids and messagebox.askyesno("Bevestigen","Geselecteerde herinneringen verwijderen?"):
   with self.con() as c:c.executemany("DELETE FROM herinneringen WHERE id=?",[(int(i),) for i in ids])
   self.memory_page()
 def task(self,title):
  if title:
   with self.con() as c:c.execute("INSERT INTO taken(titel,status,aangemaakt) VALUES(?,?,?)",(title,"Open",datetime.now().isoformat(timespec="seconds")))
 def agent_page(self):
  self.clear();self.head("Taken & agent","Jarvis kan taken plannen. Uitvoering van systeemacties vraagt steeds jouw bevestiging.")
  row=tk.Frame(self.main,bg=BG);row.pack(fill="x",pady=(0,10))
  self.taskentry=tk.Entry(row,bg=PANEL2,fg=WHITE,insertbackground=WHITE,relief="flat",font=("Segoe UI",11));self.taskentry.pack(side="left",fill="x",expand=True,ipady=11)
  tk.Button(row,text="+ Taak",command=self.add_task_ui,bg="#087f91",fg="white",relief="flat",padx=15,pady=9).pack(side="left",padx=8)
  tk.Button(row,text="Afronden",command=self.done_task,bg=PANEL2,fg=WHITE,relief="flat",padx=13,pady=9).pack(side="left")
  self.tt=ttk.Treeview(self.main,columns=("status","title"),show="headings");self.tt.heading("status",text="STATUS");self.tt.heading("title",text="TAAK");self.tt.column("status",width=110,stretch=False);self.tt.pack(fill="both",expand=True)
  with self.con() as c:r=c.execute("SELECT id,status,titel FROM taken ORDER BY id DESC").fetchall()
  for i,s,t in r:self.tt.insert("","end",iid=str(i),values=(s,t))
  card=tk.Frame(self.main,bg=PANEL,padx=16,pady=14);card.pack(fill="x",pady=12)
  tk.Label(card,text="Veilige acties",bg=PANEL,fg=WHITE,font=("Segoe UI",12,"bold")).pack(anchor="w")
  tk.Label(card,text="Programma starten en projectmap aanmaken zijn beschikbaar via bevestigde knoppen. Geen vrije shell- of PowerShell-uitvoering.",bg=PANEL,fg=MUTED,wraplength=800).pack(anchor="w",pady=6)
  r=tk.Frame(card,bg=PANEL);r.pack(anchor="w")
  for label,cmd in [("Kladblok starten",lambda:self.launch(["notepad.exe"])),("Rekenmachine starten",lambda:self.launch(["calc.exe"])),("Jarvis-map openen",lambda:subprocess.Popen(["explorer",str(ROOT)]))]:
   tk.Button(r,text=label,command=cmd,bg=PANEL2,fg=WHITE,relief="flat",padx=10,pady=8).pack(side="left",padx=(0,7))
 def add_task_ui(self):
  x=self.taskentry.get().strip()
  if x:self.task(x);self.agent_page()
 def done_task(self):
  ids=self.tt.selection()
  if ids:
   with self.con() as c:c.executemany("UPDATE taken SET status='Afgerond' WHERE id=?",[(int(i),) for i in ids])
   self.agent_page()
 def launch(self,cmd):
  if messagebox.askyesno("Toestemming","Wil je dit programma starten?"):subprocess.Popen(cmd)
 def voice_page(self):
  self.clear();self.head("Spraakbediening","Optionele lokale spraakmodules. De installatie is apart en vereist internet om pakketten te downloaden.")
  card=tk.Frame(self.main,bg=PANEL,padx=20,pady=20);card.pack(fill="x")
  tk.Label(card,text="Spraakherkenning (Whisper) en gesproken antwoord (pyttsx3)",bg=PANEL,fg=WHITE,font=("Segoe UI",12,"bold")).pack(anchor="w")
  tk.Label(card,text="Deze basisversie bevat nog geen actieve microfoonlus. Gebruik het installatiebestand om de lokale spraakbibliotheken klaar te zetten; daarna volgt de microfoonintegratie als afzonderlijke veilige stap.",bg=PANEL,fg=MUTED,wraplength=800,justify="left").pack(anchor="w",pady=10)
  tk.Button(card,text="Test luidspreker (Windows)",command=lambda:self.launch(["ms-settings:sound"]),bg="#087f91",fg="white",relief="flat",padx=12,pady=9).pack(anchor="w")
 def settings_page(self):
  self.clear();self.head("Instellingen & privacy","Lokale verwerking en bestaande database.")
  card=tk.Frame(self.main,bg=PANEL,padx=20,pady=20);card.pack(fill="x")
  for k,v in [("Model",MODEL),("Ollama",API),("Database",str(DB)),("Gegevens","Lokale SQLite-database"),("Geheugen","Voorstellen worden pas na jouw toestemming opgeslagen"),("Computeracties","Beperkte lijst, altijd met bevestiging")]:
   tk.Label(card,text=k.upper(),bg=PANEL,fg=MUTED,font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(7,0));tk.Label(card,text=v,bg=PANEL,fg=WHITE).pack(anchor="w")
 def status_check(self):
  def run():
   try:
    with urllib.request.urlopen(TAGS,timeout=4) as r:data=json.loads(r.read().decode())
    ok=any(m.get("name","").split(":")[0]==MODEL.split(":")[0] for m in data.get("models",[]))
    txt="● OLLAMA VERBONDEN • QWEN BESCHIKBAAR" if ok else "● OLLAMA VERBONDEN • MODEL NIET GEVONDEN"; col=GREEN if ok else "#ff7182"
   except:txt,col="● OLLAMA NIET VERBONDEN","#ff7182"
   self.root.after(0,lambda:self.status.config(text=txt,fg=col))
  threading.Thread(target=run,daemon=True).start();self.root.after(20000,self.status_check)

if __name__=="__main__":
 root=tk.Tk();app=Jarvis(root);root.mainloop()
