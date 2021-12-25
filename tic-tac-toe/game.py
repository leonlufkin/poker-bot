import numpy as np
from utils import TicTacToe, Config
from demo_players import BasicPlayer, RandomPlayer
from CFR_player import CFRPlayer

def run_game(config, verbose=True):
    if config.num_players != 2:
        raise RuntimeError("need exactly 2 players, have {:d}".format(config.num_players))

    players = config.get_players()
    Game = TicTacToe(width=config.width, num_players=config.num_players)

    player = -1
    while not Game.is_game_over(player):
        player = (player + 1) % config.num_players
        move = players[player].get_move(Game.get_game_state())
        Game.add_move(move, player)
        if verbose:
            print("Player {}".format(player))
            print(Game.board)

    if Game.has_tictactoe(player):
        if verbose:
            print("{} won the game!".format(config.names[player]))
        return config.names[player]
    else:
        if verbose:
            print("It's a tie!")
        return "tie"

if __name__ == '__main__':
    config = Config(width=3)
    config.register_player("Random Player", RandomPlayer())
    # config.register_player("Basic Player", BasicPlayer())
    config.register_player("CFR Player", CFRPlayer())

    num_runs = int(1e1)
    game_results = np.empty(num_runs, dtype="S13")
    for run in range(num_runs):
        game_results[run] = run_game(config, verbose=False)
    
    players, counts = np.unique(game_results, return_counts=True)
    for player, count in zip(players, counts):
        print("{}: {:d}/{:d} ({:.3f})".format(player.decode('utf-8'), count, num_runs, count/num_runs))

        