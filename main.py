from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from game import Game
from leaderboard import Leaderboard
import json

active_games  = []
boards = []
application = None

# Commands
async def  start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("started, bip bop 0_0")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/join - start a new game or join the existing one\n" +\
                                    "/status - check if there is an active game session\n" +\
                                    "/leaderboard - see who is the greates player in this chat")

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global application
    global active_games

    message_type = update.message.chat.type
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username
    chat_id = update.message.chat_id

    if message_type == "private" : await update.message.reply_text("you can only start a game in a group chat ;)"); return
    if user_name is None: await update.message.reply_text("you'll need to creat a username before you can play :("); return

    if(not(game_exists(chat_id))):
        active_games.append(Game({user_name: None}, chat_id))
        await update.message.reply_text("we need one more player")
        await application.bot.send_message(chat_id=user_id, text="type rock, paper or scissors")
    else:
        if player_joined(get_game(chat_id), user_name):
            if len(get_game(chat_id).players_values) == 1:
                await update.message.reply_text("we need one more player")
                if get_game(chat_id).players_values[user_name] is None: await application.bot.send_message(chat_id=user_id, text="type rock, paper or scissors")
            else:
                await update.message.reply_text("the game has started, proceed to choose your option in private messages with me")
                if get_game(chat_id).players_values[user_name] is None: await application.bot.send_message(chat_id=user_id, text="type rock, paper or scissors")
        else:
            if len(get_game(chat_id).players_values) == 1:
                get_game(chat_id).players_values[user_name] = None
                await update.message.reply_text("the game has started, proceed to choose your option in private messages with me")
                await application.bot.send_message(chat_id=user_id, text="type rock, paper or scissors")
            else:
                await update.message.reply_text("game is in action right now, please wait")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_games

    message_type = update.message.chat.type
    chat_id = update.message.chat_id

    if message_type == "private": await update.message.reply_text("you'll need to go in to a group chat for that one ;)"); return

    if game_exists(chat_id):
        if len(get_game(chat_id).players_values) == 1:
            await update.message.reply_text("we are waiting for one more player to join")
        else:
            await update.message.reply_text("players are thinking what to choose :0")
    else:
        await update.message.reply_text("there is no active game session right now, start a new game with /join command")

async def  leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    chat_id = update.message.chat_id

    if message_type == "private": await update.message.reply_text("you'll need to go in to a group chat for that one ;)"); return

    if board_exists(chat_id): await update.message.reply_text(form_board(chat_id))
    else: await update.message.reply_text("this chat has no leaderboard")

# Responses
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_games
    global application

    message_type = update.message.chat.type
    user_name = update.message.from_user.username
    text = update.message.text.lower()
    player_not_fond = True

    if message_type == "private":
        for game in active_games:
            if user_name in list(game.players_values.keys()):
                player_not_fond = False
                if make_choice(game.chat_id, user_name, text):
                    await application.bot.send_message(chat_id=game.chat_id, text=f"@{user_name} made a decision!")
                    if everybody_is_ready(game.chat_id):
                       await update.message.reply_text("game is complete, go back to the group to see the results :)")
                       await end_game(game.chat_id)
                    else: await update.message.reply_text("great choice! now wait for the other player to decide")
                else: await update.message.reply_text("type rock, paper or scissors >:(")
    if player_not_fond: await update.message.reply_text("you are not in a game, you can join in a group chat using /join command")

    # Debug info
    # print(f"user {user_name} writes {text} in chat {update.message.chat_id}")
    # for game in active_games: print(game)


# Functions (game)
async def end_game(chat_id):
    global application
    global active_games
    
    game: Game = get_game(chat_id)

    A_player = list(game.players_values.keys())[0]
    B_player = list(game.players_values.keys())[1]
    A_emoji = create_emoji(game.players_values[A_player])
    B_emoji = create_emoji(game.players_values[B_player])

    text = f"@{A_player} : {game.players_values[A_player]}{A_emoji}\n" +\
           f"@{B_player} : {game.players_values[B_player]}{B_emoji}\n" +\
           f"result : "

    if game.players_values[A_player] == game.players_values[B_player]: text += "draw :)"
    if game.players_values[A_player] == "rock" and game.players_values[B_player] == "paper": text += f"@{B_player} has won!"; add_player_to_board(B_player, chat_id)
    if game.players_values[A_player] == "rock" and game.players_values[B_player] == "scissors": text += f"@{A_player} has won!"; add_player_to_board(A_player, chat_id)
    if game.players_values[A_player] == "paper" and game.players_values[B_player] == "rock": text += f"@{A_player} has won!"; add_player_to_board(A_player, chat_id)
    if game.players_values[A_player] == "paper" and game.players_values[B_player] == "scissors": text += f"@{B_player} has won!"; add_player_to_board(B_player, chat_id)
    if game.players_values[A_player] == "scissors" and game.players_values[B_player] == "rock": text += f"@{B_player} has won!"; add_player_to_board(B_player, chat_id)
    if game.players_values[A_player] == "scissors" and game.players_values[B_player] == "paper": text += f"@{A_player} has won!"; add_player_to_board(A_player, chat_id)

    await application.bot.send_message(chat_id=chat_id, text = text)
    active_games.pop(get_game_index(chat_id))



def game_exists(chat_id):
    global active_games
    for game in active_games:
        if chat_id == game.chat_id: return True
    return False

def get_game(chat_id) -> Game:
    global active_games
    for game in active_games:
        if chat_id == game.chat_id: return game
    return None

def get_game_index(chat_id):
    global active_games
    for i in range(len(active_games)):
        if chat_id == active_games[i].chat_id: return i
    return None

def player_joined(game: Game, user_name):
    if user_name in list(game.players_values.keys()): return True
    return False

def make_choice(chat_id, user_name, text):
    choice_made = False
    if "rock" in text: get_game(chat_id).players_values[user_name] = "rock"; choice_made = True
    elif "paper" in text: get_game(chat_id).players_values[user_name] = "paper"; choice_made = True
    elif "scissors" in text: get_game(chat_id).players_values[user_name] = "scissors"; choice_made = True
    return choice_made

def everybody_is_ready(chat_id):
    game: Game = get_game(chat_id)
    if any(val is None for val in game.players_values.values()) or (len(game.players_values) == 1): return False
    return True

def create_emoji(option):
    if option == "rock": return "🪨"
    if option == "paper": return "📄"
    if option == "scissors": return "✂️"

# Functions (boards)
def get_board(chat_id) -> Leaderboard:
    global boards
    for b in boards:
        if b.chat_id == chat_id: return b
    return None

def board_exists(chat_id):
    global boards
    for b in boards:
        if b.chat_id == chat_id: return True
    return False

def add_player_to_board(user_name, chat_id):
    global boards
    if(board_exists(chat_id)):
        board = get_board(chat_id)
        board.stats[user_name] = board.stats.setdefault(user_name, 0) + 1
    else: boards.append(Leaderboard({user_name : 1}, chat_id))
    save_all_boards()

def form_board(chat_id):
    board = sorted(get_board(chat_id).stats.items(), key = lambda x: x[1], reverse = True)
    text = "leaderboard:\n"
    for user in board:
        text += f"@{user[0]} has won {user[1]} times\n"
    return text

def save_all_boards():
    global boards
    boards_dict = [board.to_dict() for board in boards]
    with open("leaderboards.json", "w", encoding = "utf-8") as save_file:
        json.dump(boards_dict, save_file, indent = 4)

def read_all_boards():
    global boards
    with open("leaderboards.json", "r", encoding = "utf-8") as save_file:
        boards_data = json.load(save_file)
    boards = [Leaderboard(stats = board["stats"], chat_id = board["chat_id"]) for board in boards_data]

# Main
def main():
    print("Starting bot...", flush = True)
    global application

    token = "ENTER YOUR TOKEN HERE"
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Load Data
    read_all_boards()

    print("Telegram Bot started!", flush=True)
    application.run_polling()
   


if __name__ == '__main__':
    main()