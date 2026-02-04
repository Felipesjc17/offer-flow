import sqlite3
import os

# O nome do arquivo do banco de dados
DB_FILE = "deals.db"
DB_PATH = os.path.join(os.getcwd(), DB_FILE)

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    Inicializa o banco de dados e cria a tabela 'deals' se ela não existir.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Cria a tabela para armazenar os links das ofertas já postadas
        # O LINK é a chave primária para evitar duplicatas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                link TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print(">>> Banco de dados inicializado com sucesso.")
    except sqlite3.Error as e:
        print(f">>> Erro ao inicializar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()

def deal_exists(deal_link):
    """
    Verifica se uma oferta com o mesmo link já existe no banco de dados.
    
    Args:
        deal_link (str): O link da oferta a ser verificado.
        
    Returns:
        bool: True se a oferta já existe, False caso contrário.
    """
    exists = False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM deals WHERE link = ?", (deal_link,))
        result = cursor.fetchone()
        
        if result:
            exists = True
            
    except sqlite3.Error as e:
        print(f">>> Erro ao verificar a oferta no banco de dados: {e}")
    finally:
        if conn:
            conn.close()
    return exists

def add_deal(deal_link, deal_title):
    """
    Adiciona o link de uma nova oferta ao banco de dados.
    
    Args:
        deal_link (str): O link da oferta.
        deal_title (str): O título da oferta.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insere o link, ignorando se ele já existir (por segurança, embora a verificação seja feita antes)
        cursor.execute("INSERT OR IGNORE INTO deals (link, title) VALUES (?, ?)", (deal_link, deal_title))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f">>> Erro ao adicionar a oferta ao banco de dados: {e}")
    finally:
        if conn:
            conn.close()

def clean_old_deals(hours=24):
    """
    Remove ofertas do banco de dados que são mais antigas que o limite de horas.
    Isso permite que ofertas sejam repostadas após esse período.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DELETE FROM deals WHERE post_date < datetime('now', '-{hours} hours')")
        
        count = cursor.rowcount
        conn.commit()
        if count > 0:
            print(f">>> Limpeza: {count} ofertas expiradas (> {hours}h) foram removidas do banco.")
    except sqlite3.Error as e:
        print(f">>> Erro ao limpar ofertas antigas: {e}")
    finally:
        if conn:
            conn.close()
