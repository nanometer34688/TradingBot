import requests
import os
from dotenv import load_dotenv

load_dotenv()

class DiscordBot:
    def __init__(self) -> None:
        self.WEBHOOK = os.getenv('WEBHOOK')     
        print("Loaded Discord Webhook: ", self.WEBHOOK)
        self.test_connection()
        

    def test_connection(self):
        print("\n", "#"*10, "\n", "DISCORD START", "\n", "#"*10, "\n")
        print("Testing webhook")
        resp = self.send_message("Starting Trading Bot")
        if resp.status_code == 204:
            print("Connected to DISCORD")
        else:
            print("Issue connecting to DISCORD:", resp)
        print("\n", "#"*10, "\n", "DISCORD END", "\n", "#"*10, "\n")

    def send_message(self, message):
        data = {"content": message}
        response = requests.post(self.WEBHOOK, json=data)
        return response