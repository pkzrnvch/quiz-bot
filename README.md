# Quiz bot

You can use this bot to run quizzes. It can send questions, check whether the user's answer is correct, and reveal the correct answer if user gives up. 

Bot works with [Telegram](https://telegram.org/) and [vk.com](https://vk.com/).

## How to install
- Download project files and create virtual environment.
- Create an `.env` file in the project directory. Create a new telegram bot through a [BotFather](https://telegram.me/BotFather) and assign its token to `TG_BOT_TOKEN` variable.
- Send a message to [@UserInfoBot](https://t.me/userinfobot) to get your chat_id, assign it to `TG_LOGS_CHAT_ID` variable to receive log messages.
- Get your VK group API key from group's settings page and assign it to `VK_GROUP_API_KEY` variable.
- Set up a [Redis](https://redis.com/) account. After that, create a database, its host, port and password parameters can be found in configuration tab. Assign these values to `REDIS_DB_HOST`, `REDIS_DB_PORT`, `REDIS_DB_PASSWORD` variables respectively.
- Download archive with quiz questions and answers from [here](https://dvmn.org/media/modules_dist/quiz-questions.zip) for demonstration purposes. Your own files should also follow the same format, unless you change the loading script.

Example of an `.env` file:
```
TG_BOT_TOKEN='Telegram bot token'
TG_LOGS_CHAT_ID='Telegram chat id to send log messages'
VK_GROUP_API_KEY='VK group api key'
REDIS_DB_HOST='Redis database host'
REDIS_DB_PORT='Redis database port'
REDIS_DB_PASSWORD='Redis database password'
QUIZ_FILE_PATH='Path to your file with quiz questions ans answers'
```

Python3 should already be installed. Use pip (or pip3, in case of conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```

### Usage

To run the bots locally use the following commands from the project directory:
```
python telegram_bot.py
```
```
python vk_bot.py
```

### Project Goals

The code is written for educational purposes on online-course for web-developers [Devman](https://dvmn.org).