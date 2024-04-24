from tgtg import TgtgClient
from json import load
import requests
import schedule
import time
from decouple import Config, RepositoryEnv

# Load credentials
def load_credentials():
    try:
        config = Config(RepositoryEnv('.env'))
        credentials = {
            'email': config.get('TGTG_EMAIL'),
            'telegram': {
                'bot_chatID1': config.get('TELEGRAM_BOT_CHATID1'),
                'bot_chatID2': config.get('TELEGRAM_BOT_CHATID1'),
                'bot_token': config.get('TELEGRAM_BOT_TOKEN')
            }
        }
        return credentials
    except Exception as e:
        print(f"Failed to load credentials: {e}")
        return None

# Initialize TGTG client
def initialize_tgtg_client(credentials):
    try:
        client = TgtgClient(email=credentials['email'])
        tgtg_credentials = client.get_credentials()
        client = TgtgClient(access_token=tgtg_credentials['access_token'],
                            refresh_token=tgtg_credentials['refresh_token'],
                            user_id=tgtg_credentials['user_id'],
                            cookie=tgtg_credentials['cookie'])
        return client
    except Exception as e:
        print(f"Failed to initialize TGTG client: {e}")
        return None

# Send message via Telegram bot
def send_telegram_message(bot_message, chat_ids):
    try:
        for chat_id in chat_ids:
            bot_token = credentials['telegram']['bot_token']
            send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={bot_message}'
            response = requests.get(send_text)
            response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False

# Fetch stock from TGTG API
def fetch_stock(client):
    try:
        api_response = client.get_items()
        return api_response
    except Exception as e:
        print(f"Failed to fetch stock from TGTG API: {e}")
        return None

# Process stock data
def process_stock(stock_data):
    try:
        processed_data = []
        for item in stock_data:
            processed_item = {
                'item_id': item['item']['item_id'],
                'store_name': item['store']['store_name'],
                'items_available': item['items_available'],
                'category_picture': item['store']['cover_picture']['current_url']
            }
            processed_data.append(processed_item)
        return processed_data
    except Exception as e:
        print(f"Failed to process stock data: {e}")
        return None

# Initialize credentials and client
credentials = load_credentials()
if credentials:
    client = initialize_tgtg_client(credentials)
else:
    exit(1)

# Initialize favourites in stock
favourites_in_stock = []

# Telegram bot message functions
def send_text_message(bot_message):
    chat_ids = [credentials['telegram']['bot_chatID1'], credentials['telegram']['bot_chatID2']]
    return send_telegram_message(bot_message, chat_ids)

def send_image_message(image_url, image_caption=None):
    chat_ids = [credentials['telegram']['bot_chatID1'], credentials['telegram']['bot_chatID2']]
    try:
        for chat_id in chat_ids:
            bot_token = credentials['telegram']['bot_token']
            send_text = f'https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id={chat_id}&photo={image_url}'
            if image_caption:
                send_text += f'&caption={image_caption}'
            response = requests.get(send_text)
            response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send Telegram image message: {e}")
        return False

# Main routine check function
def routine_check():
    global favourites_in_stock
    stock_data = fetch_stock(client)
    if stock_data:
        new_stock = process_stock(stock_data)
        if new_stock:
            list_of_item_ids = [fav['item_id'] for fav in new_stock]
            for item_id in list_of_item_ids:
                try:
                    old_stock = next(item['items_available'] for item in favourites_in_stock if item['item_id'] == item_id)
                except StopIteration:
                    old_stock = 0
                    print("Item ID was not known as a favorite before")
                new_stock_count = next(item['items_available'] for item in new_stock if item['item_id'] == item_id)

                if new_stock_count != old_stock:
                    if old_stock == 0 and new_stock_count > 0:
                        message = f"There are {new_stock_count} new goodie bags at {next(item['store_name'] for item in new_stock if item['item_id'] == item_id)}"
                        image = next(item['category_picture'] for item in new_stock if item['item_id'] == item_id)
                        send_image_message(image, message)
                    elif old_stock > new_stock_count and new_stock_count != 0:
                        pass
                    elif old_stock > new_stock_count and new_stock_count == 0:
                        message = f"⭕ Sold out! There are no more goodie bags available at {next(item['store_name'] for item in new_stock if item['item_id'] == item_id)}"
                        send_text_message(message)
                    else:
                        message = f"There was a change of number of goodie bags in stock from {old_stock} to {new_stock_count} at {next(item['store_name'] for item in new_stock if item['item_id'] == item_id)}"
                        send_text_message(message)

            favourites_in_stock = new_stock
            print(f"API run at {time.ctime(time.time())} successful. Current stock:")
            for item_id in list_of_item_ids:
                print(f"{next(item['store_name'] for item in new_stock if item['item_id'] == item_id)}: {next(item['items_available'] for item in new_stock if item['item_id'] == item_id)}")
    else:
        print("Failed to fetch stock data")

# Main still alive function
def still_alive():
    try:
        message = f"Current time: {time.ctime(time.time())}. The bot is still running. "
        list_of_item_ids = [fav['item_id'] for fav in favourites_in_stock]
        for item_id in list_of_item_ids:
            message += f"{next(item['store_name'] for item in favourites_in_stock if item['item_id'] == item_id)}: {next(item['items_available'] for item in favourites_in_stock if item['item_id'] == item_id)} items available"
        send_text_message(message)
    except Exception as e:
        print(f"Failed to send 'still alive' message: {e}")

# Schedule jobs
try:
    schedule.every(3).minutes.do(routine_check)
except Exception as e:
    print(f"Failed to schedule routine_check: {e}")

try:
    schedule.every(24).hours.do(still_alive)
except Exception as e:
    print(f"Failed to schedule still_alive: {e}")

# Initial message
initial_message = "The bot script has started successfully. The bot checks every 3 minutes if there is something new at TooGoodToGo. Every 24 hours, the bot sends a 'still alive' message."
if not send_text_message(initial_message):
    exit(1)

# Main loop
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        exit(1)
