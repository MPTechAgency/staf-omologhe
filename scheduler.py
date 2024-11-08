from apscheduler.schedulers.background import BackgroundScheduler
from app import get_db_connection
from datetime import datetime, timedelta

def check_expiring_documents():
    conn = get_db_connection()
    oggi = datetime.now()
    prossimo_mese = oggi + timedelta(days=30)
    documenti = conn.execute('SELECT * FROM documenti WHERE data_scadenza BETWEEN ? AND ?', (oggi, prossimo_mese)).fetchall()
    
    for doc in documenti:
        print(f"Alert: Il documento di {doc['nome_produttore']} sta per scadere il {doc['data_scadenza']}")
    
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(check_expiring_documents, 'interval', days=1)
scheduler.start()
