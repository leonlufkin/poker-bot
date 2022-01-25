from copy import deepcopy

class InvalidMoveError(ValueError):
   """raised when user attempts an invalid move"""
   pass

class Move:
    def __init__(self, move, amount=0, actor=None):
        self.validate_move(move, amount)
        self.move = move
        self.amount = amount
        self.actor = actor
    
    def validate_move(self, move, amount):
        if move not in ["fold", "call", "check", "raise"]:
            raise InvalidMoveError("invalid move type {}, must be one of 'fold', 'call', 'check', or 'raise'".format(move))
        if move == "raise":
            if amount <= 0:
                raise InvalidMoveError("cannot raise {}, must raise a strictly positive amount".format(amount))

class BettingState:
    def __init__(self, names: list, playing, active, bets, pot, chip_stacks, shares, betting_round, last_raiser):
        self.names = names
        self.playing = playing
        self.active = active
        self.bets = bets
        self.pot = pot
        self.chip_stacks = chip_stacks
        self.shares = shares
        self.betting_round = betting_round
        self.name = None
        self.seat = None
        self.last_raiser = last_raiser

    def add_player_info(self, name, seat):
        c = deepcopy(self)
        c.name = name
        c.seat = seat
        return c

class BettingRound:
   def __init__(self, names: list, playing, active, chip_stacks, shares, pot):
      num_players = len(names)
      self.betting_state = BettingState(
         names=names,
         playing=playing,
         active=active,
         bets=np.zeros(num_players),
         pot=pot,
         chip_stacks=chip_stacks,
         shares=shares,
         shares=shares,
         betting_round=0,
         last_raiser=names[-1]
      )

   def add_player_move(self, name, move: Move, verbose=False):
      max_bet = self.betting_state.bets.max()
      if move.move == "fold":
         if verbose:
            print("{} folds!".format(name))
         self.betting_state.playing[name] = self.betting_state.active[name] = False
         return 0
      elif move.move == "call":
         call_amount = max_bet - self.betting_state.bets[name]
         if call_amount >= self.betting_state.chip_stacks[name]:
            if verbose:
               print("{} calls and is all in!".format(name))
            self.betting_state.bets[name] = self.betting_state.chip_stacks[name] + self.betting_state.bets[name]
            self.betting_state.active[name] = False
            return self.betting_state.chip_stacks[name]
         else:
            if verbose:
               print("{} calls!".format(name))
            self.betting_state.bets[name] = max_bet
            return call_amount
      elif move.move == "check":
         if self.betting_state.bets[name] < max_bet:
            raise InvalidMoveError("{} attempted to check when they needed to bet {} more to match {}".format(self.names[seat], max_bet-self.bets[seat], max_bet))
         if verbose:
            print("{} checks!".format(name))
         return 0
      else:
         if move.amount > self.betting_state.chip_stacks[name]:
            raise InvalidMoveError("{} attempted to bet {} when they only have {}!".format(name, move.amount, self.chip_stacks[i]))
         elif move.amount + self.betting_state.bets[name] <= max_bet:
            raise InvalidMoveError("{} attempted to raise {} when they must raise at least {} to not call, check, or fold".format(self.names[seat], move.amount, max_bet-self.bets[seat]+1))
         elif move.amount == self.betting_state.chip_stacks[name]:
            if verbose:
               print("{} is all in!".format(name))
            self.betting_state.active[name] = False
            self.last_raiser = name
            return self.betting_state.chip_stacks[name]
         else:
            if verbose:
               print("{} raises by {}!".format(name, move.amount))
            self.betting_state.bets[name] += move.amount
            self.last_raiser = name
            return move.amount

      def round(self):

