from mytgtgclient import MyTgtgClient
from json import load, dump
import requests
import schedule
import time
import os

# For remote deployment, the credentials are stored as environment variables in Heroku
# Try to load the credentials remotely first. If this fails, look for a local file
credentials_remote_loaded = False

try:
    # Credential handling for Heroku
    credentials = dict()
    credentials['email'] = os.environ['TGTG_EMAIL']
    print(f"tgtg_email: {credentials['email']}")

    telegram = dict()
    telegram['bot_chatID1'] = os.environ['TELEGRAM_BOT_CHATID1']
    print(f"TELEGRAM_BOT_CHATID1: {telegram['bot_chatID1']}")
    telegram['bot_chatID2'] = os.environ['TELEGRAM_BOT_CHATID2']
    print(f"TELEGRAM_BOT_CHATID2: {telegram['bot_chatID2']}")
    telegram['bot_token'] = os.environ['TELEGRAM_BOT_TOKEN']
    print(f"TELEGRAM_BOT_TOKEN: {telegram['bot_token']}")

    credentials_remote_loaded = True
except KeyError:
    print("No credentials found in Heroku environment")

if not credentials_remote_loaded:
    try:
        # Credential handling for local version
        # Load Telegram account credentials from a hidden file
        with open('telegram.json') as f:
            telegram = load(f)

        # Load TGTG account credentials from a hidden file
        with open('credentials.json') as f:
            credentials = load(f)
    except FileNotFoundError:
        print("No files found for local credentials.")

# Create the TGTG client with my credentials
client = MyTgtgClient(email=credentials['email'])

# Retrieve and save the TGTG credentials
tgtg_credentials = client.get_credentials()

# Re-create the client with the retrieved credentials
client = MyTgtgClient(
    access_token=tgtg_credentials['access_token'],
    refresh_token=tgtg_credentials['refresh_token'],
    user_id=tgtg_credentials['user_id'],
    cookie_datadome=tgtg_credentials['cookie']
)

# Init the favourites in stock list as a global variable
favourites_in_stock = list()

def telegram_bot_sendtext(bot_message, only_to_admin=False):
    """
    Helper function: Send a message with the specified Telegram bot.
    It can be specified if both users or only the admin receives the message.
    Follow this article to figure out a specific chatID: https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-messages-with-python-4cf314d9fa3e
    """
    chatIDlist = [telegram["bot_chatID1"]] if only_to_admin else [telegram["bot_chatID1"], telegram["bot_chatID2"]]
    bot_token = telegram["bot_token"]

    for chat_id in chatIDlist:
        send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={bot_message}'
        response = requests.get(send_text)

    return response.json()

def telegram_bot_sendimage(image_url, image_caption=None):
    """
    For sending an image in Telegram, that can also be accompanied by an image caption.
    """
    chatIDlist = [telegram["bot_chatID1"], telegram["bot_chatID2"]]
    bot_token = telegram["bot_token"]

    for chat_id in chatIDlist:
        send_text = f'https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id={chat_id}&photo={image_url}'
        if image_caption:
            send_text += f'&caption={image_caption}'
        response = requests.get(send_text)

    return response.json()

def fetch_stock_from_api(api_result):
    """
    For filtering out the important information from the API response.
    """
    new_api_result = []
    for item in api_result:
        current_fav = {
            'item_id': item['item']['item_id'],
            'store_name': item['store']['store_name'],
            'items_available': item['items_available'],
            'category_picture': item['store']['cover_picture']['current_url']
        }
        new_api_result.append(current_fav)
    return new_api_result

def routine_check():
    """
    Function that gets called via schedule every 3 minutes.
    Retrieves the data from TGTG API and selects the message to send.
    """
    try:
        global favourites_in_stock

        if not first_run:
            tgtg_client.login()

        # Get all favorite items
        api_response = client.get_items()
        new_api_result = fetch_stock_from_api(api_response)

        # Go through all favourite items and compare the stock
        list_of_item_ids = [fav['item_id'] for fav in new_api_result]
        for item_id in list_of_item_ids:
            old_stock = next((item['items_available'] for item in favourites_in_stock if item['item_id'] == item_id), 0)
            new_stock = next(item['items_available'] for item in new_api_result if item['item_id'] == item_id)

            # Check if the stock has changed and send a message if so
            if new_stock != old_stock:
                if old_stock == 0 and new_stock > 0:
                    message = f"There are {new_stock} new goodie bags at {next(item['store_name'] for item in new_api_result if item['item_id'] == item_id)}"
                    image = next(item['category_picture'] for item in new_api_result if item['item_id'] == item_id)
                    telegram_bot_sendimage(image, message)
                elif old_stock > new_stock and new_stock == 0:
                    message = f"⭕ Sold out! There are no more goodie bags available at {next(item['store_name'] for item in new_api_result if item['item_id'] == item_id)}."
                    telegram_bot_sendtext(message)
                else:
                    message = f"There was a change of number of goodie bags in stock from {old_stock} to {new_stock} at {next(item['store_name'] for item in new_api_result if item['item_id'] == item_id)}."
                    telegram_bot_sendtext(message)

        # Reset the global information with the newest fetch
        favourites_in_stock = new_api_result

        # Print out some maintenance info in the terminal
        print(f"API run at {time.ctime(time.time())} successful. Current stock:")
        for item in new_api_result:
            print(f"{item['store_name']}: {item['items_available']}")
    except Exception as e:
        telegram_bot_sendtext("Something went wrong somewhere", only_to_admin=True)
        print(f"An error occurred: {e}")

def still_alive():
    """
    This function gets called every 24 hours and sends a 'still alive' message to the admin.
    """
    try:
        message = f"Current time: {time.ctime(time.time())}. The bot is still running. "

        global favourites_in_stock
        for item in favourites_in_stock:
            message += f"{item['store_name']}: {item['items_available']} items available. "

        telegram_bot_sendtext(message, only_to_admin=True)
    except Exception as e:
        telegram_bot_sendtext("Something went wrong somewhere", only_to_admin=True)
        print(f"An error occurred: {e}")

# Use schedule to set up a recurrent checking
try:
    schedule.every(3).minutes.do(routine_check)
    schedule.every(24).hours.do(still_alive)

    # Description of the service that gets sent once
    telegram_bot_sendtext("The bot script has started successfully. The bot checks every 3 minutes if there is something new at TooGoodToGo. Every 24 hours, the bot sends a 'still alive'-message.", only_to_admin=True)
except Exception as e:
    telegram_bot_sendtext("Something went wrong somewhere", only_to_admin=True)
    print(f"An error occurred: {e}")

while True:
    try:
        # run_pending
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        telegram_bot_sendtext("Something went wrong somewhere", only_to_admin=True)
        print(f"An error occurred: {e}")
