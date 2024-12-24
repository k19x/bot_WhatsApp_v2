import sqlite3
from requests import post, get
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from os import getlogin
import time
import logging
from requests import post
from typing import Optional

# Configuração do banco de dados SQLite
DB_NAME = f"c:\\Users\\{getlogin()}\\Downloads\\whatsapp_monitor.db"


def setup_database():
    """Cria o banco de dados e a tabela caso não exista."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


def get_last_message():
    """Obtém a última mensagem armazenada no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message, time FROM messages ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result


def save_message(message, time):
    """Salva a mensagem e o horário no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (message, time) VALUES (?, ?)", (message, time)
    )
    conn.commit()
    conn.close()



# Configuração do logging
logging.basicConfig(level=logging.INFO)

# Função para chamar a API
def api(number: str) -> Optional[str]:
    url = "https://donodozap.com:443/api/verify"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        "Content-Type": "application/json",
    }
    json = {"phone": f"55{number}"}
    try:
        response = post(url, headers=headers, json=json, timeout=10)
        response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP 4xx/5xx
        try:
            return response.json()["accounts"][0]["NOME"]
        except (ValueError, KeyError) as e:
            logging.error("Erro ao decodificar JSON na resposta: %s", e)
            return None
    except Exception as e:
        logging.error("Erro na chamada da API: %s", e)
        return None


# Configuração do Selenium
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument(
    f"--user-data-dir=C:\\Users\\{getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
)
chrome_options.add_argument("--disable-gpu")

# Configuração inicial
setup_database()

try:
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://web.whatsapp.com/")
    print("Carregando WhatsApp Web com sessão ativa...")

    user = "Teste Bot"  # Grupo WhatsApp

    # Espera o chat específico carregar
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, f'//span[@dir="auto"][@title="{user}"]')
        )
    ).click()

    # Aguarda as mensagens carregarem
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]'))
    )

    # Loop para monitorar mensagens continuamente
    while True:
        try:
            # Localiza todas as mensagens recebidas
            messages = driver.find_elements(
                By.XPATH, '//div[contains(@class, "message-in")]'
            )

            if messages:
                last_message = messages[-1]

                # Captura o texto e o horário da última mensagem
                text_element = last_message.find_element(
                    By.XPATH,
                    './/span[contains(@class, "selectable-text copyable-text")]',
                )
                time_element = last_message.find_element(
                    By.XPATH,
                    '//span[@class="x1rg5ohu x16dsc37"][@dir="auto"]',  # Ajuste conforme necessário
                )

                last_message_text = text_element.text
                last_message_time_text = time_element.text

                # Obtém a última mensagem do banco de dados
                db_message = get_last_message()

                # Compara a mensagem atual com a última armazenada no banco de dados
                if not db_message or (
                    db_message[0] != last_message_text
                    or db_message[1] != last_message_time_text
                ):
                    print(
                        f"Nova mensagem às {last_message_time_text}: {last_message_text}"
                    )
                    save_message(last_message_text, last_message_time_text)

                    if last_message_text.startswith("#phone"):
                        phone_number = last_message_text[7:]
                        logging.info(f"Processando o número de telefone: {phone_number}")
                        
                        try:
                            response = api(phone_number)
                            logging.info(f"Resposta da API: {response}")
                        except Exception as e:
                            logging.error(f"Erro ao chamar a API: {e}")
                            response = "desconhecido"
                        
                        try:
                            # Responde no chat
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located(
                                    (
                                        By.XPATH,
                                        '//div[@contenteditable="true"][@tabindex="10"][@role="textbox"]',
                                    )
                                )
                            ).send_keys(
                                f"O número {phone_number} pertence a {response}\n"
                            )
                            logging.info("Mensagem enviada com sucesso.")
                        except Exception as e:
                            logging.error(f"Erro ao enviar a mensagem: {e}")

            time.sleep(2)  # Aguarda 2 segundos antes de verificar novamente
        except Exception as e:
            print(f"Erro ao monitorar mensagens: {e}")
            time.sleep(5)

except Exception as e:
    print(f"Erro no script: {e}")
finally:
    if "driver" in locals():
        driver.quit()
