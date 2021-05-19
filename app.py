import asyncio
import pandas
import json
import os
import copy
import uuid

from quart import Quart, websocket, send_from_directory, redirect
from quart import render_template

app = Quart(__name__)

def load_game_questions(file):
    df = pandas.read_csv(file)
    
    cats = list(set(df["Category"].values))

    cats.remove("Final Jeopardy")
    final_jeop = list(df[df["Category"] == "Final Jeopardy"][["Question", "Answer", "Score"]].values[0])
    final_jeop += [0, "Final Jeopardy"]
    
    cat_ids = list(range(len(cats)))

    game = {}

    for cat_id,cat in zip(cat_ids, cats):
        qu = df[df["Category"] == cat]["Question"].values
        ans = df[df["Category"] == cat]["Answer"].values
        score = df[df["Category"] == cat]["Score"].values
        key = list(range(len(qu)))

        game[cat_id] = {"name": cat, "questions": {k: [q, a, s, 0, k, cat_id] for (k,q,a,s) in zip(key, qu, ans, score)}}

    max_num_questions = max([len(game[cat]["questions"]) for cat in game])

    board = [
        [game[cat_id]["questions"].get(key, "NULL") for cat_id in game if cat_id != "Final Jeopardy"] for key in range(max_num_questions)
    ]

    return {"Final Jeopardy": final_jeop, "board": board, "categories": cats}

def get_cell(board, key, cat_id):
    return board[int(key)][int(cat_id)]

all_games = {}
current_games = {}

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/game/make/<gamelabel>/')
async def makegame(gamelabel):
    roomname = str(uuid.uuid4().fields[-1])[:5]
    current_games[roomname] = copy.deepcopy(all_games[gamelabel])

    return redirect(os.path.join("/game", roomname), code=302)

@app.route('/game/<gamename>/')
async def game(gamename):
    return await render_template("game.html", all_games=current_games, gamename=gamename)

@app.route('/q/<gamename>/<cat_id>/<key>/')
async def question(gamename, cat_id, key):
    if gamename not in current_games:
        return "Game Not Found!"

    get_cell(current_games[gamename]["board"], key, cat_id)[3] = 1

    return await render_template("question.html", key=key, question=get_cell(current_games[gamename]["board"], key, cat_id)[0], gamename=gamename, cat_id=cat_id)


@app.route('/a/<gamename>/<cat_id>/<key>/')
async def answer(gamename, cat_id, key):
    if gamename not in current_games:
        return "Game Not Found!"

    return await render_template("answer.html", key=key, answer=get_cell(current_games[gamename]["board"], key, cat_id)[1], gamename=gamename, cat_id=cat_id)

@app.route('/fq/<gamename>')
async def finalquestion(gamename):
    if gamename not in current_games:
        return "Game Not Found!"

    return await render_template("finalquestion.html", question=current_games[gamename]["Final Jeopardy"][0], gamename=gamename)

@app.route('/fa/<gamename>')
async def finalanswer(gamename):
    if gamename not in current_games:
        return "Game Not Found!"

    answer = copy.deepcopy(current_games[gamename]["Final Jeopardy"][1])
    del current_games[gamename]

    return await render_template("finalanswer.html", question=answer, gamename=gamename)

@app.route('/')
async def welcome():
    return await render_template("welcome.html", games=list(all_games.keys()))

    
@app.route('/home')
async def home_welcome():
    return await render_template("welcome.html", games=list(all_games.keys()))

if __name__ == '__main__':

    res_dir = os.path.join(app.root_path, 'static/res')
    for file in os.listdir(res_dir):
        all_games[os.path.splitext(file)[0]] = load_game_questions(os.path.join(res_dir, file))
    
    print("LOADING GAMES: ", all_games.keys())


    app.run()
