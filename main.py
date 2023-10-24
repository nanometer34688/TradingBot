from utils import oanda, discord_client
from dotenv import load_dotenv
import os 
from strategy import Silver_Bullet
load_dotenv() # Load .env file

access_token = os.getenv('OANDA_API')

oanda_client = oanda.Oanda(access_token=access_token)
oanda_client.choose_account()

def start_trading(instrument):
    r = oanda_client.get_live_pricing(instrument)
    discord_bot = discord_client.DiscordBot() # Used to notify me when it makes a trade
    # Define any strategy here
    SB = Silver_Bullet.SilverBullet(oanda_client, discord_bot)
    while True:
        SB.look_for_trades()

start_trading("SPX500_USD")