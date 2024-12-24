from requests import post, get
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
verify = False


def api(number):
    url = "https://donodozap.com:443/api/verify"
    headers = {
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
        "Content-Type": "application/json",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        "Accept": "*/*",
        "Origin": "https://donodozap.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://donodozap.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i",
        "Connection": "keep-alive",
    }
    json = {"phone": f"{number}"}
    try:
        response = post(url, headers=headers, json=json, proxies=proxies, verify=verify)
        if response.status_code == 200:
            try:
                return response.json()['accounts'][0]['NOME']
            except ValueError:
                print("Erro ao decodificar JSON na resposta.")
                return None
        else:
            print(f"Falha na API. Status: {response.status_code}")
    except Exception as e:
        print(f"Erro na chamada da API: {e}")


chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument(
    "--user-data-dir=C:\\Users\\Caique\\AppData\\Local\\Google\\Chrome\\User Data"
)
chrome_options.add_argument("--disable-gpu")

try:
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://web.whatsapp.com/")
    print("Carregando WhatsApp Web com sessão ativa...")

    # Espera o chat específico carregar
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//span[@dir="auto"][@title="Pentest Zup - Itaú"]')
        )
    ).click()

    # Aguarda as mensagens carregarem
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]'))
    )

    last_seen_message = None  # Variável para controlar a última mensagem processada

    # Loop para monitorar mensagens continuamente
    while True:
        try:
            # Localiza todas as mensagens recebidas
            messages = driver.find_elements(
                By.XPATH, '//div[contains(@class, "message-in")]'
            )

            if messages:
                last_message = messages[-1]
                text_element = last_message.find_element(
                    By.XPATH, './/span[@class="_ao3e selectable-text copyable-text"]'
                )
                last_message_text = text_element.text

                # Processa apenas mensagens novas
                if last_message_text != last_seen_message:
                    print(f"Nova mensagem: {last_message_text}")
                    last_seen_message = last_message_text

                    if last_message_text.startswith("#phone"):
                        print(f"{last_message_text[7:]}")
                        print(f"{api(last_message_text[7:])}")

                        # //div[@contenteditable="true"][@tabindex="10"][@role="textbox"]
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located(
                                (By.XPATH, '//div[@contenteditable="true"][@tabindex="10"][@role="textbox"]')
                            )
                        ).send_keys(
                            f"o número {last_message_text[7:]} pertence a {api(last_message_text[7:])}\n"
                        )

            time.sleep(2)  # Aguarda 2 segundos antes de verificar novamente
        except Exception as e:
            print(f"Erro ao monitorar mensagens: {e}")
            time.sleep(5)

except Exception as e:
    print(f"Erro no script: {e}")
finally:
    if "driver" in locals():
        driver.quit()
