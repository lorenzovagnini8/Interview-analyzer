import os
from supabase import create_client, Client

def get_supabase_client(url: str, key: str) -> Client:
    return create_client(url, key)

def salva_analisi(data: dict, media_type: str, supabase_url: str, supabase_key: str) -> dict:
    """
    Inserisce un nuovo record di analisi nella tabella interview_analyses di Supabase.
    """
    supabase = get_supabase_client(supabase_url, supabase_key)
    
    punteggi = data.get("punteggi", {})
    analisi = data.get("analisi", {})
    profilo = data.get("profilo_psicologico", {})
    
    payload = {
        "speaker_name": data.get("nome_intervistato", "Sconosciuto"),
        "speaker_role": data.get("ruolo", "Non specificato"),
        "team": data.get("squadra"),
        "media_type": media_type,
        
        "score_qualita_totale": punteggi.get("score_qualita_intervista"),
        "score_verbale": punteggi.get("punteggio_verbale"),
        "score_paraverbale": punteggi.get("punteggio_paraverbale"),
        "score_non_verbale": punteggi.get("punteggio_non_verbale"),
        
        "analisi_verbale": analisi.get("verbale"),
        "analisi_paraverbale": analisi.get("paraverbale"),
        "analisi_non_verbale": analisi.get("non_verbale"),
        
        "tratti_chiave": profilo.get("tratti_chiave", []),
        "descrizione_psicologica": profilo.get("descrizione_sintetica"),
        "livello_stress": profilo.get("livello_stress_percepito")
    }
    
    res = supabase.table("interview_analyses").insert(payload).execute()
    return res.data

def carica_storico_analisi(supabase_url: str, supabase_key: str):
    """
    Recupera tutte le analisi salvate ordinate per data di creazione.
    """
    supabase = get_supabase_client(supabase_url, supabase_key)
    res = supabase.table("interview_analyses").select("*").order("created_at", desc=True).execute()
    return res.data
