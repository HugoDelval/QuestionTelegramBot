from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram
import telegram.ext
import logging
import os

from model import Poll, Answer, Vote, Voter

FORMATTER = logging.Formatter("%(asctime)s {%(module)s:%(funcName)s:%(lineno)d} [%(levelname)s] %(message)s")
HANDLER = logging.StreamHandler()
HANDLER.setFormatter(FORMATTER)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(logging.DEBUG)

QUESTION_CMD = """/question "Ta (très pertinente) question ?" "Choix 1" "Choix 2" ["D'autres choix si tu veux" ...]"""
WELCOME_TEXT = """
Salut {{name}},

Lance une question en utilisant:
{cmd}

Utilise /help à tout moment pour plus d'info.

Bisous
""".format(cmd=QUESTION_CMD)

token = os.getenv("TOKEN")


def _reconstruct_args(args: [str], separator='"'):
    returned_args = []
    current = ""
    for arg in args:
        if current and arg.endswith(separator):
            returned_args.append(current + " " + arg[:-1])
            current = ""
            continue
        if current:
            current += " " + arg
            continue
        if arg.startswith(separator):
            current += arg[1:]
            if arg.endswith(separator):
                returned_args.append(current[:-1])
                current = ""
            continue
        returned_args.append(arg)

    return returned_args


def generate_poll_message(poll: Poll, answers: [Answer]) -> str:
    created_by = "Quel dilemme ! Aide-nous à choisir :"
    question = poll.question
    answers_text = ""
    for a in answers:
        votes = a.votes
        votes_str = ""
        if votes:
            votes_str = " ({} 👍 : {})".format(len(votes), ", ".join([v.voter.name for v in votes]))
        answers_text += "- {}{}\n".format(a.answer, votes_str)
    text = "{}\n\n*{}*\n\n{}".format(created_by, question, answers_text)
    reply_markup = telegram.InlineKeyboardMarkup([
        [telegram.InlineKeyboardButton(a.answer, callback_data=str(a.id))] for a in answers
    ])
    return text, reply_markup


def show_poll(poll: Poll, answers: [Answer], update: telegram.ext.Dispatcher, bot: telegram.Update):
    question = poll.question
    text, reply_markup = generate_poll_message(poll, answers)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.MARKDOWN)


def start_callback(bot: telegram.Update, update: telegram.ext.Dispatcher):
    name = update.message.from_user.first_name
    LOGGER.info("{} started the bot".format(name))
    update.message.reply_text(WELCOME_TEXT.format(name=name))


def question_callback(bot: telegram.Update, update: telegram.ext.Dispatcher, args: [str]):
    args = _reconstruct_args(args)
    LOGGER.debug("'Question' called with {args}".format(args=args))
    if len(args) < 3:
        update.message.reply_text("Il n'y a pas assez d'arguments:\n\n{}".format(QUESTION_CMD))
        return
    new_poll = Poll.create(question=args[0])
    answers = []
    for answer in args[1:]:
        answers.append(Answer.create(poll=new_poll, answer=answer))
    show_poll(new_poll, answers, update, bot)


def insert_or_update_voter(voter_id: int, voter_name: str):
    try:
        voter = Voter.get_by_id(voter_id)
    except Voter.DoesNotExist:
        voter = Voter.create(id=voter_id, name=voter_name)
        return voter
    if voter.name != voter_name:
        voter.name = voter_name
        voter.save()
    return voter


def vote_callback(bot, update):
    answer_id = update.callback_query.data
    voter_name = update.callback_query.from_user.username
    voter_id = update.callback_query.from_user.id
    LOGGER.info("{} ({}) voted {}".format(voter_name, voter_id, answer_id))
    voter = insert_or_update_voter(voter_id, voter_name)
    try:
        answer = Answer.get_by_id(answer_id)
    except Answer.DoesNotExist:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Je n'ai pas trouvé cette réponse dans ma BDD")
        return
    try:
        vote = Vote.get((Vote.voter == voter) & (Vote.answer == answer))
        # Vote already exists, lets delete it
        vote.delete_instance()
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Ton vote a bien été supprimé")
    except Vote.DoesNotExist:
        # Vote does not exist, lets create it
        Vote.create(answer=answer, voter=voter)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Ton vote a bien été enregistré")
    # Update question text
    poll = answer.poll
    answers = poll.answers
    text, reply_markup = generate_poll_message(poll, answers)
    bot.editMessageText(
        message_id=update.callback_query.message.message_id,
        chat_id=update.callback_query.message.chat.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=telegram.ParseMode.MARKDOWN,
    )

updater = Updater(token)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start_callback))
dispatcher.add_handler(CommandHandler("question", question_callback, pass_args=True))
dispatcher.add_handler(CallbackQueryHandler(vote_callback))

if __name__ == "__main__":
    LOGGER.info("Starting bot")
    updater.start_polling()
    updater.idle()
