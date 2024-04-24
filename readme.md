
## WatchBot for "too good to go"
### Problem
This project helps me to no longer miss my favorite offers at "[too good to go](https://toogoodtogo.de/de)" (also known as tgtg)!

"Too good to go" is a platform, where stores can offer bags of leftover food, that they otherwise need to throw away. The stores save a little bit of money, we get goods, that already have a few quirks, but are still consumable. Most importantly, this reduces food waste and thereby is good for the planet. In my neighborhood, e.g. a supermarket offers fruits & vegetables and a bakery offer their leftover bread at the end of the day.

However, the tgtg-app does often not notify me in time when my favorite goods are in stock. Since the offers are popular and limited, I regularly miss the time to click and collect the items. There are no settings for notifications in the app.

### Solution
This application scrapes info from the tgtg-app and sends me a notification via a Telegram bot as soon as my favorite items are available. The application runs in the cloud via heroku. It can also run in AWS free tier. 
Here is a screenshot of the application:

![Telegram Screenshot](/result_screenshot.jpeg "Telegram bot with notifications")

##### Tgtg API
There is a library wrapped around the API of the tgtg-app. You can find the library and a short documentation [here.](https://pypi.org/project/tgtg/)

##### Telegram bot
I used Telegram as the service to notify me, because they are quite supportive for adding your own bots to the platform and provide a rich API. [This article](https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-messages-with-python-4cf314d9fa3e) provides a quick introduction into sending Telegram messages with python.

You can create a new bot using @BotFather. Simply start a conversation with @BotFather and send /newbot. You will receive an API token for the bot. Enter this token in your config. On the next start, the scanner will help you obtain the chat_id.

For more information about the @BotFather please refer to the official documentation: https://core.telegram.org/bots#6-botfather

##### Heroku Deployment
Heroku is a platform to run small web applications in the cloud for free. [This article](https://medium.com/dev-genius/how-to-deploy-your-python-script-to-heroku-in-4-minutes-cddf11d852af) gives a short description on how to deploy a python script on Heroku. Additionally, I used config variables to hide my credentials in the project. These variables are explained [here](https://devcenter.heroku.com/articles/config-vars#config-var-policies) in the heroku documentation.

##### AWS free tier
As of 2023, Heroku does not offer free tier anymore so I switched to aws free tier with ec2 deployment. I followed the steps here: https://python.plainenglish.io/deploying-python-scripts-on-aws-a-step-by-step-guide-for-installing-selenium-and-chromedriver-13c1ef23c5b4
Create a .env file with the following params:
TGTG_EMAIL=<your_email>
TELEGRAM_BOT_CHATID1=<your_chat id>
TELEGRAM_BOT_TOKEN=<your_telegram token>


Many thanks to @Der-henning and @AukiJuanDiaz
