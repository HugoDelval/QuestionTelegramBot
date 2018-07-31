from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram
import telegram.ext
import logging

from model import Poll, Answer

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

Utilise /aide à tout moment pour plus d'info.

Bisous
""".format(cmd=QUESTION_CMD)


with open("token") as f:
    token = f.read().strip()


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


def show_poll(poll: Poll, answers: [Answer], update: telegram.ext.Dispatcher, bot: telegram.Update):
    created_by = "Une nouvelle question a été créée par {}:".format(update.message.from_user.first_name)
    question = poll.question
    answers_text = "\n".join(["{}. {}".format(i, a.answer) for i, a in enumerate(answers)])
    reply_markup = telegram.InlineKeyboardMarkup([
        [telegram.InlineKeyboardButton(a.answer, callback_data=str(a.id))] for a in answers
    ])
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="{}\n\n{}\n\n{}".format(created_by, question, answers_text),
                    reply_markup=reply_markup)


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


def vote_callback(bot, update):
    answer_id = update.callback_query.data
    voter = update.callback_query.from_user.username
    LOGGER.info("{} voted {}".format(voter, answer_id))
    answer = Answer.get_by_id(answer_id)
    if not answer:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Je n'ai pas trouvé cette réponse dans ma BDD")
        return
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                            text="Reçu {}".format(answer.answer))


updater = Updater(token)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start_callback))
dispatcher.add_handler(CommandHandler("question", question_callback, pass_args=True))
dispatcher.add_handler(CallbackQueryHandler(vote_callback))

if __name__ == "__main__":
    LOGGER.info("Starting bot")
    updater.start_polling()
    updater.idle()
