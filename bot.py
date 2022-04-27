from datetime import datetime, timedelta
import json
import logging
import os
import re
import smtplib
import ssl
import sys

from dotenv.main import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler
)
from constants import CONFIRM_CITIES, KEYWORDS, CHOOSE_CITIES, CHOOSE_STATE, CHOOSE_CATEGORY, REQUEST_PERIOD

from conversations import bye, cancel, category_handler, city_handler, confirm_cities, get_searches, keywords_handler, period_handler, resume, start, stop, timeout, state_handler

from craigslist import CraigslistForSale

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
smtp_server = "smtp.gmail.com"

# Create a secure SSL context
ssl_context = ssl.create_default_context()


def main():
    """Init app and start the bot"""

    # Create the Updater and pass it your bots token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    api_key: str = os.getenv(
        'API_KEY_DEV' if 'DEBUG' in sys.argv else 'API_KEY')
    updater = Updater(api_key, use_context=True)

    # Add conversation handler with the states
    conversation_handler = ConversationHandler(
        conversation_timeout=120,
        entry_points=[
            CommandHandler(
                'start', start
            ),
            CommandHandler(
                'stop', stop
            ),
            CommandHandler(
                'resume', resume
            ),
            CommandHandler(
                'bye', bye
            ),
            CommandHandler(
                'mysearches', get_searches
            )
        ],
        states={
            CHOOSE_STATE: [
                CallbackQueryHandler(state_handler)
            ],
            CHOOSE_CITIES: [
                CallbackQueryHandler(city_handler)
            ],
            CONFIRM_CITIES: [
                CallbackQueryHandler(confirm_cities)
            ],
            KEYWORDS: [
                CallbackQueryHandler(keywords_handler),
                MessageHandler(Filters.text & ~(
                    Filters.command), keywords_handler)
            ],
            CHOOSE_CATEGORY: [
                CallbackQueryHandler(category_handler)
            ],
            REQUEST_PERIOD: [
                CallbackQueryHandler(period_handler)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(None, timeout)
            ]
        },
        fallbacks=[
            CommandHandler(
                'cancel', cancel
            )
        ]
    )

    # schedule the checking for scheduled searches
    j = updater.job_queue
    j.run_repeating(scheduled_search, interval=timedelta(seconds=15))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # Add handler to dispatcher
    dispatcher.add_handler(conversation_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def scheduled_search(context: CallbackContext) -> None:
    """Every minute, we search for searchs to perform"""

    # read the data from teh JSON file
    data = None
    with open('jobs.json') as json_file:
        data = json.load(json_file)

    for key in data:
        if data[key]['is_stopped']:
            continue

        # if we have have already executed this the first time, and we do not have to do it rn, skip

        if data[key]['last_search_at']:
            search_time = datetime.fromisoformat(
                data[key]['last_search_at'])
            search_time += timedelta(minutes=int(data[key]['period']))
            if search_time > datetime.now():
                continue

        # update the last search at
        data[key]['last_search_at'] = datetime.now().isoformat()

        # update the data file
        with open('jobs.json', 'w') as json_file:
            json.dump(data, json_file)

        # execute any pending jobs
        # one search per city
        for city in data[key]['cities']:
            cl_search = CraigslistForSale(
                site=city['value'],
                area=None,
                category=data[key]['category'],
                filters={'query': data[key]['keywords']}
            )

            approx_result_count = cl_search.get_results_approx_count()
            if not approx_result_count or approx_result_count == 0:
                context.bot.send_message(
                    chat_id=data[key]['chat_id'],
                    text=f'👀 Oops..\n\nYour search for "{data[key]["keywords"]}" in {city["text"]} is empty\n\nWe could not find anything 😥'
                )
                continue

            context.bot.send_message(
                chat_id=data[key]['chat_id'],
                text=f'The results you requested 👇'
            )

            for result in cl_search.get_results(sort_by='newest', geotagged=True, limit=5):
                context.bot.send_message(
                    chat_id=data[key]['chat_id'],
                    text=f'{result["name"]}\nPrice: {result["price"]}\n\nWhere: {result["geotag"] if "geotag" in result else "No location"}\n\nURL:{result["url"]}'
                )

            context.bot.send_message(
                chat_id=data[key]['chat_id'],
                text=f'These are the results from your scheduled search in {city["text"]} 👆\n\nYou are receiving these results every {data[key]["period"]} minutes'
            )

        context.bot.send_message(
            chat_id=data[key]['chat_id'],
            text=f'Use /stop to stop receiving these results'
        )


if __name__ == '__main__':
    main()
