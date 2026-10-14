import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Definizione dello Schema Pydantic per forzare l'output JSON di Gemini
class ProfiloPsicologico(BaseModel):
    tratti_chiave: List[str] = Field(description="Elenco di 3-5 tratti di personalità chiave osservati")
    descrizione_sintetica: str = Field(description="Breve descrizione del profilo psicologico e comportamentale")
    livello_stress_percepito: str = Field(description="Valutazione del livello di stress/pressione: Basso, Medio, Alto")

class AnalisiDettagliata(BaseModel):
    verbale: str = Field(description="Analisi del contenuto, scelta delle parole, pertinenza e chiarezza")
    paraverbale: str = Field(description="Analisi di tono della voce, ritmo, pause ed esitazioni vocali")
    non_verbale: str = Field(description="Analisi del linguaggio del corpo, contatto visivo e gestualità (se video)")

class PunteggiQualita(BaseModel):
    score_qualita_intervista: float = Field(description="Punteggio complessivo di qualità dell'intervista da 1.0 a 10.0")
    punteggio_verbale: float = Field(description="Voto sulla comunicazione verbale da 1.0 a 10.0")
    punteggio_paraverbale: float = Field(description="Voto sulla comunicazione paraverbale da 1.0 a 10.0")
    punteggio_non_verbale: float = Field(description="Voto sulla comunicazione non verbale da 1.0 a 10.0")

class ReportIntervista(BaseModel):
    nome_intervistato: str
    ruolo: str = Field(description="Allenatore, Giocatore o Dirigente")
    squadra: Optional[str] = None
    punteggi: PunteggiQualita
    analisi: AnalisiDettagliata
    profilo_psicologico: ProfiloPsicologico

# 2. Funzione principale per analizzare il file con Gemini
def analizza_intervista(file_path: str, mime_type: str, api_key: str) -> dict:
    """
    Carica il file multimediale (audio/video/testo) su Gemini API
    ed estrae l'analisi psicologica e comunicativa strutturata.
    """
    client = genai.Client(api_key=api_key)
    
    # Caricamento del file tramite File API (consigliato per audio e video)
    print(f"Caricamento file {file_path} in corso...")
    uploaded_file = client.files.upload(file=file_path)
    
    prompt = """
    Sei un esperto di psicologia dello sport, analisi del linguaggio non verbale e comunicazione per il calcio.
    Analizza l'intervista fornita tenendo conto di tutti i livelli di comunicazione accessibili:
    1. VERBALE: Contenuto, scelta dei termini, concetti espressi, gestione delle domande scomode.
    2. PARAVERBALE: Tono della voce, ritmo, pause, esitazioni, volume.
    3. NON VERBALE: Gestualità, contatto visivo, postura ed espressioni facciali (se presente video).

    Genera una valutazione della qualità dell'intervista e traccia un profilo psicologico dettagliato dell'intervistato.
    """

    print("Analisi con Gemini in corso...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReportIntervista,
            temperature=0.2
        )
    )
    
    # Rimuovi il file temporaneo dai server di Gemini dopo l'elaborazione
    client.files.delete(name=uploaded_file.name)
    
    return json.loads(response.text)
