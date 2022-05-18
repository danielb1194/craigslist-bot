from datetime import datetime
import json
from sre_parse import CATEGORIES
from time import strftime
from unicodedata import category
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    ConversationHandler
)

from constants import CONFIRM_CITIES, CRAIGSLIST_CATEGORIES, KEYWORDS, CHOOSE_CITIES, CHOOSE_STATE, SELECT_CATEGORY, PRICE, REQUEST_PERIOD, STATES

data = None
with open('jobs.json') as json_file:
    data = json.load(json_file)


def start(update: Update, context: CallbackContext):
    """Ask the user for information on a new query"""

    state_buttons = [state.button() for state in STATES.values()]

    keyboard = [
        state_buttons,
        [InlineKeyboardButton("Cancel", callback_data='cancel')],
    ]

    update.message.reply_text(
        text='Hello There 👋\n\nTo start your search, please choose a State from the options 🗺️',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CHOOSE_STATE


def state_handler(update: Update, context: CallbackContext) -> int:
    """Saves the user choice for a state and prompts the user to choose a city"""

    query = update.callback_query
    query.answer()

    if query.data == 'cancel':
        return cancel()

    if query.data == 'continue':
        keyboard = []
        for city in data[str(update.effective_chat.id)]:
            keyboard.append(
                InlineKeyboardButton(
                    text=city['text'],
                    callback_data=city['value']
                )
            )

        query.edit_message_text(
            text='Confirm your cities 📍\n\nTap on any to remove it 🗑️',
            reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM_CITIES

    if str(update.effective_chat.id) not in data:
        data[str(update.effective_chat.id)] = {}
    data[str(update.effective_chat.id)]['state'] = query.data

    keyboard = []
    for city in STATES[data[str(update.effective_chat.id)]['state']].cities:
        if 'cities' in data[str(update.effective_chat.id)].keys() and city in data[str(update.effective_chat.id)]['cities']:
            continue
        keyboard.append([InlineKeyboardButton(
            text=city['text'],
            callback_data=city['value']
        )])

    if 'cities' in data[str(update.effective_chat.id)].keys():
        keyboard.append([InlineKeyboardButton(
            "Continue ➡️", callback_data='continue'),
            InlineKeyboardButton("Cancel", callback_data='cancel')]
        )
    else:
        keyboard.append([InlineKeyboardButton(
            "Cancel", callback_data='cancel')]
        )

    query.edit_message_text(
        text=f'Awesome!\n\n{STATES[data[str(update.effective_chat.id)]["state"]].text} it is 🗺️\n\nNow please tap the cities you want to add 📍',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CHOOSE_CITIES


def city_handler(update: Update, context: CallbackContext) -> int:

    query = update.callback_query
    query.answer()

    if query.data == 'cancel':
        return cancel()

    if query.data == 'continue':
        keyboard = []
        for city in data[str(update.effective_user.id)]['cities']:
            keyboard.append([
                InlineKeyboardButton(
                    text=f'❌ {city["text"]}',
                    callback_data=city['value']
                )
            ])
        keyboard.append(
            [InlineKeyboardButton("Confirm ✅", callback_data='confirm'),
             InlineKeyboardButton("🔙 Add another city", callback_data='back')]
        )
        keyboard.append(
            [InlineKeyboardButton("Cancel", callback_data='cancel')]
        )

        query.edit_message_text(
            text='Excellent!\n\nTap "Confirm" to confirm your choices ✅\n\nTap any city to remove it from the list 🗑️\n\nTap Back to go back to adding cities 🔙',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CONFIRM_CITIES

    if query.data == 'choose_state':
        state_buttons = [state.button() for state in STATES.values()]

        keyboard = [
            state_buttons,
            [InlineKeyboardButton("Cancel", callback_data='cancel')],
        ]

        query.edit_message_text(
            text='Choose a state to continue 🗺️',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CHOOSE_STATE

    # list every city in every state the user has chosen
    chosen_city = [city for city in STATES[data[str(
        update.effective_chat.id)]['state']].cities if city['value'] == query.data][0]

    if 'cities' not in data[str(update.effective_chat.id)]:
        data[str(update.effective_chat.id)]['cities'] = []

    data[str(update.effective_chat.id)]['cities'].append(chosen_city)

    # create the cities keyboard (remove the chosen cities from the list)
    keyboard = []
    for city in STATES[data[str(update.effective_chat.id)]['state']].cities:
        if city in data[str(update.effective_chat.id)]['cities']:
            continue
        keyboard.append([InlineKeyboardButton(
            text=city['text'], callback_data=city['value'])])
    keyboard.append(
        [InlineKeyboardButton("Continue ➡️", callback_data='continue'),
         InlineKeyboardButton("Choose another state 🗺️", callback_data='choose_state')]
    )
    keyboard.append([InlineKeyboardButton("Cancel", callback_data='cancel')])

    query.edit_message_text(
        text=f'Tap any other city you want to add 📍',
        reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSE_CITIES


def confirm_cities(update: Update, context: CallbackContext) -> int:
    """prompts the user to confirm the cities chosen, or delete any choice"""

    query = update.callback_query
    query.answer()

    if query.data == 'cancel':
        return cancel()

    if query.data == 'confirm':
        data[str(update.effective_chat.id)]['keywords'] = dict()

        query.edit_message_text(
            text='Perfect! Now please type the keywords for your search 🔎',
            reply_markup=None
        )

        return KEYWORDS

    if query.data == 'back':
        keyboard = []
        for city in STATES[data[str(update.effective_chat.id)]['state']].cities:
            if city in data[str(update.effective_chat.id)]['cities']:
                continue
            keyboard.append([InlineKeyboardButton(
                text=city['text'],
                callback_data=city['value'])
            ])
        keyboard.append(
            [InlineKeyboardButton("Continue ➡️", callback_data='continue'),
             InlineKeyboardButton("Choose another state 🗺️", callback_data='choose_state')]
        )
        keyboard.append([InlineKeyboardButton(
            "Cancel", callback_data='cancel')])

        query.edit_message_text(
            text=f'Tap any other city you want to add 📍',
            reply_markup=InlineKeyboardMarkup(keyboard))

        return CHOOSE_CITIES

    # remove the tapped city from the cities list
    chosen_city = [city for city in data[str(
        update.effective_chat.id)]['cities'] if city['value'] == query.data][0]
    data[str(update.effective_chat.id)]['cities'].remove(chosen_city)

    if len(data[str(update.effective_chat.id)]['cities']) == 0:
        keyboard = []
        for city in STATES[data[str(update.effective_chat.id)]['state']].cities:
            if city in data[str(update.effective_chat.id)]['cities']:
                continue
            keyboard.append([InlineKeyboardButton(
                text=city['text'], callback_data=city['value'])])
        keyboard.append(
            [InlineKeyboardButton("Continue ➡️", callback_data='continue'),
             InlineKeyboardButton("Choose another state 🗺️", callback_data='choose_state')]
        )
        keyboard.append([InlineKeyboardButton(
            "Cancel", callback_data='cancel')]
        )

        query.edit_message_text(
            text=f'Tap any other city you want to add 📍\n\nYou need to pick at least one city to continue 👇',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CHOOSE_CITIES

    keyboard = []
    for city in data[str(update.effective_user.id)]['cities']:
        keyboard.append([
            InlineKeyboardButton(
                text=f'❌ {city["text"]}',
                callback_data=city['value']
            )
        ])
    keyboard.append(
        [InlineKeyboardButton("Confirm ✅", callback_data='confirm'),
            InlineKeyboardButton("🔙 Add another city", callback_data='back')]
    )
    keyboard.append(
        [InlineKeyboardButton("Cancel", callback_data='cancel')]
    )

    query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CONFIRM_CITIES


def keywords_handler(update: Update, context: CallbackContext) -> int:
    """handles the user """

    # if we entered the handle via query
    query = update.callback_query
    user_data = data[str(update.effective_chat.id)]

    if query:
        query.answer()

        if query.data == 'cancel':
            return cancel()

        if query.data == 'done':
            if len(user_data['keywords']) < 1:
                keyboard = [
                    [InlineKeyboardButton("✅ Done", callback_data='done'),
                     InlineKeyboardButton("Cancel", callback_data='cancel')]
                ]

                query.edit_message_text(
                    text=f'You need to send at least one keyword 🤖',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return KEYWORDS

            keyboard = [
                [InlineKeyboardButton("5 minutes", callback_data='5'),
                    InlineKeyboardButton("10 minutes", callback_data='10')],
                [InlineKeyboardButton("15 minutes", callback_data='15'),
                    InlineKeyboardButton("30 minutes", callback_data='30')],
                [InlineKeyboardButton("60 minutes", callback_data='60'),
                    InlineKeyboardButton("90 minutes", callback_data='90')],
                [InlineKeyboardButton("Just return the results now", callback_data='no_period'),
                    InlineKeyboardButton("Cancel", callback_data='cancel')]
            ]

            query.edit_message_text(
                text=f'Looking good! 😎\n\nNow if you want to periodically search this, choose a time period for your search ⌚',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return REQUEST_PERIOD

        if query.data in user_data['keywords']:
            # remove the tapped keyword from the dict
            user_data['keywords'].pop(query.data)

            keyboard = []
            for kw in user_data['keywords']:
                keyboard.append(
                    [
                        InlineKeyboardButton(f'❌ {kw}', callback_data=kw),
                        InlineKeyboardButton(
                            f'💲 Limit {user_data["keywords"][kw]["max_price"]}', callback_data=kw + ':max_price'),
                        InlineKeyboardButton(
                            CRAIGSLIST_CATEGORIES[user_data['keywords'][kw]['category']].capitalize(), callback_data=kw + ':category')
                    ]
                )

            keyboard.append(
                [InlineKeyboardButton("✅ Done", callback_data='done'),
                 InlineKeyboardButton("Cancel", callback_data='cancel')]
            )

            query.edit_message_text(
                text=f'🗑️ Removed your keyword: "{query.data}"\n\nTap "✅ Done" to continue or send another keyword\n\nModify the max price or the cateogry by tapping them 👉',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return KEYWORDS

        data_split = query.data.split(":")
        # save the keyword the user selected
        user_data['selected_keyword'] = data_split[0]
        if 'category' == data_split[1]:
            # prompt the user to select a category for this keyword
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=CRAIGSLIST_CATEGORIES[category].capitalize(),
                        callback_data=category)
                ] for category in CRAIGSLIST_CATEGORIES
            ]
            query.edit_message_text(
                text="Please select the cateogry you wat to search in 👇",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return SELECT_CATEGORY

        if 'max_price' == data_split[1]:
            # prompt the user to send a price limit for this search
            keyboard = [
                [InlineKeyboardButton('No limit', callback_data='no_limit')]
            ]
            query.edit_message_text(
                text="Plese send me a price limit (Numbers only! 🔢)",
                reply_markup=InlineKeyboardMarkup(keyboard))
            return PRICE

    else:
        # save the message from the user to the keywords
        # the way we save it is as a dict, with the keyword beign the key, and the value beign the price limit
        data[str(update.effective_chat.id)
             ]['keywords'][update.message.text] = {
                 'category': 'foa',
                 'max_price': None
        }

    keyboard = []
    for kw in user_data['keywords']:
        keyboard.append(
            [
                InlineKeyboardButton(f'❌ {kw}', callback_data=kw),
                InlineKeyboardButton(
                    f'💲 Limit {user_data["keywords"][kw]["max_price"]}', callback_data=kw + ':max_price'),
                InlineKeyboardButton(
                    CRAIGSLIST_CATEGORIES[user_data['keywords'][update.message.text]['category']].capitalize(), callback_data=kw + ':category')
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("✅ Done", callback_data='done'),
         InlineKeyboardButton("Cancel", callback_data='cancel')]
    )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'💾 Saved your keyword: "{update.message.text}"\n\nTap "✅ Done" to continue or send me another keyword\n\nModify the max price or the cateogry by tapping them 👉',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return KEYWORDS


def price_handler(update: Update, context: CallbackContext) -> int:
    """Handles the user inputting a price limit for the search"""

    query = update.callback_query
    user_data = data[str(update.effective_chat.id)]

    if query:
        query.answer()

        if query.data == 'cancel':
            return cancel()

        # prepare the keyboard
        keyboard = [
            [InlineKeyboardButton("No limit", callback_data='no_limit'),
             InlineKeyboardButton("Cancel", callback_data='cancel')]
        ]
        query.edit_message_text(
            text="Send me the price limit you want for this keyword",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        if query.data == 'no_limit':
            query.edit_message_text(
                text=f"Awesome! No 💲 limit on the search for {user_data['selected_keyword']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    else:
        # check that the message contains only numbers
        if not update.message.text.isnumeric():
            context.bot.send_message(
                "Please only use numbers when setting up a price limit",
                reply_markup=InlineKeyboardMarkup(
                    [InlineKeyboardButton("✅ Done", callback_data='done'),
                     InlineKeyboardButton("Cancel", callback_data='cancel')]
                )
            )
            return PRICE

        # save the price limit
        user_data['keywords'][data[str(
            update.effective_chat.id)]['selected_keyword']]['max_price'] = update.message.text

        keyboard = []
        for kw in user_data['keywords']:
            keyboard.append(
                [
                    InlineKeyboardButton(f'❌ {kw}', callback_data=kw),
                    InlineKeyboardButton(
                        f'💲 Limit {user_data["keywords"][kw]["max_price"]}', callback_data=kw + ':max_price'),
                    InlineKeyboardButton(CRAIGSLIST_CATEGORIES[user_data['keywords']
                                                               [kw]['category']].capitalize(), callback_data=kw + ':category')
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("✅ Done", callback_data='done'),
             InlineKeyboardButton("Cancel", callback_data='cancel')]
        )

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Saved the price limit for {user_data['selected_keyword']} as \"{update.message.text}\"",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        user_data['selected_keyword'] = None

        return KEYWORDS


def category_handler(update: Update, context: CallbackContext) -> int:

    query = update.callback_query
    query.answer()

    user_data = data[str(update.effective_chat.id)]

    if query.data == 'cancel':
        return cancel()

    # save the selected category
    user_data['keywords'][
        user_data['selected_keyword']]['category'] = query.data

    keyboard = []
    for kw in user_data['keywords']:
        keyboard.append(
            [
                InlineKeyboardButton(f'❌ {kw}', callback_data=kw),
                InlineKeyboardButton(
                    f'💲 Limit {user_data["keywords"][kw]["max_price"]}', callback_data=kw + ':max_price'),
                InlineKeyboardButton(CRAIGSLIST_CATEGORIES[user_data['keywords']
                                     [kw]['category']].capitalize(), callback_data=kw + ':category')
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("✅ Done", callback_data='done'),
         InlineKeyboardButton("Cancel", callback_data='cancel')]
    )

    query.edit_message_text(
        text=f'💾 Saved your changes!\n\nTap "Done" to continue or send me another keyword\n\nModify the max price or the cateogry by tapping them 👉',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    user_data['selected_keyword'] = None

    return KEYWORDS


def period_handler(update: Update, context: CallbackContext) -> int:
    """Finally, if the user wants to periodically search, set up a schedule for it"""

    query = update.callback_query
    query.answer()

    user_data = data[str(update.effective_chat.id)]

    if query.data == 'no_period':
        # search craigslist using the given data
        pass

    # received a number, set up a schedule with the given data
    user_data['chat_id'] = update.effective_chat.id
    user_data['period'] = query.data
    user_data['created'] = datetime.now().isoformat()
    user_data['is_stopped'] = False
    user_data['last_search_at'] = None

    # write the job to jobs.json
    with open('jobs.json', 'w') as outfile:
        json.dump(data, outfile)

    query.edit_message_text(
        text=f'We are searching craigslist 🔎...'
    )

    if query.data != 'no_period':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'And have set up a schedule to look every {user_data["period"]} minutes ⏲️'
        )

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    # remove the user's data from the dictionary
    del data[str(update.effective_chat.id)]

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Operation canceled. use /start to begin searching again')

    return ConversationHandler.END


def timeout(update: Update, context: CallbackContext) -> int:
    """Handle for converation timeout and return conversation.END"""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Our conversation timed out ⌚'
    )

    return ConversationHandler.END


def bye(update: Update, context: CallbackContext) -> int:
    """Says farewell to the user."""

    update.message.reply_text(text='alrighty! Goodbye honey!')

    return ConversationHandler.END


def stop(update: Update, context: CallbackContext) -> int:
    """Stops the selected scheduled search"""

    id_str = str(update.effective_user.id)
    if not data[id_str] or data[id_str]['period'] == 'no_period':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='You dont have a periodic search in place'
        )
        return ConversationHandler.END

    if data[id_str]['is_stopped'] == True:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Your search is already stopped'
        )
        return ConversationHandler.END

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Stoped your periodic search for "{", ".join(data[id_str]["keywords"])}" 🛑'
    )

    data[id_str]['is_stopped'] = True

    data[id_str]['last_search_at'] = None

    # update the file
    with open('jobs.json', 'w') as outfile:
        json.dump(data, outfile)

    return ConversationHandler.END


def resume(update: Update, context: CallbackContext) -> int:
    """Resumes the selected user's search"""

    id_str = str(update.effective_user.id)
    if not data[id_str] or data[id_str]['period'] == 'no_period':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='You dont have any stopped periodic searches'
        )
        return ConversationHandler.END

    if data[id_str]['is_stopped'] == False:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Your search is already going'
        )
        return ConversationHandler.END

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Resuming your search! You should start getting results in a minute 🔎'
    )

    data[id_str]['is_stopped'] = False
    with open('jobs.json', 'w') as outfile:
        json.dump(data, outfile)

    return ConversationHandler.END


def get_searches(update: Update, context: CallbackContext) -> int:
    """Shows the user his searches"""

    # TODO: edit searches

    for search in data:
        if search != str(update.effective_user.id):
            continue

        cities_arr = [city['text'] for city in data[search]['cities']]
        cities_str = ", ".join(cities_arr)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Cities: {cities_str}\nKeyword(s): {data[search]["keywords"]}\nPeriod: {data[search]["period"]} minutes\nStatus: {"Stopped" if data[search]["is_stopped"] else "Active"}\nLast execution time: {data[search]["last_search_at"]} (ISO Format)'
        )

    return ConversationHandler.END
