import numpy as np  
import pandas as pd  
import matplotlib.pyplot as plt  

class Deck:

	card_types = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T"]

	def __init__(self, num_decks=6, pen_rate=0.8):
		self.num_decks = num_decks
		self.num_cards = self.num_decks * 52
		self.pen_rate = pen_rate
		self.min_cards = (1 - self.pen_rate) * self.num_cards
		self.reshuffle()

	def reshuffle(self):
		self.count = 0
		self.num_cards = self.num_decks * 52
		n = self.num_decks * 4 # number of each card type
		self.card_counts = {}
		self.cards = []
		for t in self.card_types[:-1]:
			self.card_counts[t] = n
			self.cards.extend([t] * n)
		self.card_counts[self.card_types[-1]] = n*4
		self.cards.extend([self.card_types[-1]] * (n*4))

		np.random.shuffle(self.cards)

	def deal(self):
		card = self.cards.pop() # pops last element
		self.card_counts[card] -= 1
		self.num_cards -= 1

		if card in ['2', '3', '4', '5', '6']:
			self.count += 1
		elif card in ['T', 'A']:
			self.count -= 1

		return card

class Dealer:

	scores = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10}

	def __init__(self):
		self.cards = []
		self.score = 0
		self.bust = False
		self.blackjack = False
		self.soft = False
		self.add10 = False

	def should_hit(self):
		if (self.soft and self.add10):
			return (self.score <= 17)
		else:
			return (self.score <= 16)

	def add_card(self, card):
		self.cards.append(card)
		if card == 'A':
			self.soft = True
		self.add_score(self.scores[card])

	def add_score(self, score):
		self.score += score
		if (len(self.cards) == 2) and ((((self.score == 11) and (self.soft))) or (self.score == 21)):
			self.blackjack = True
		elif self.score > 21:
			if self.add10:
				self.score -= 10
				self.add10 = False
			self.bust = (self.score > 21)
		elif (self.score <= 11) and (self.soft) and (not self.add10):
			self.score += 10
			self.add10 = True

	def reset(self):
		self.score = 0
		self.cards = []
		self.bust = False
		self.blackjack = False
		self.soft = False
		self.add10 = False

class Hand(Dealer):

	def __init__(self):
		self.cards = []
		self.score = 0
		self.bust = False
		self.blackjack = False
		self.soft = False
		self.add10 = False
		self.double = False


class Player:

	def __init__(self, capital=10000, min_betsize=10):
		self.hands = [Hand()]
		self.lose = False

		self.capital = capital
		self.min_betsize = min_betsize
		self.strategy = Strategy(self.hands[0].scores, self.min_betsize)


	def bet(self, count, num_cards):
		bet_size, true_count = self.strategy.bet(count, num_cards)
		self.bet_size = min(bet_size, self.capital)
		self.true_count = true_count

	def settle(self, win, blackjack=False, double=False):
		if win and (win != "tie"): # if win
			if blackjack:
				self.capital += (self.bet_size * 1.5)
			elif double:
				self.capital += (self.bet_size * 2)
			else:
				self.capital += self.bet_size
		elif win != "tie": # if lose
			if double:
				self.capital -= (self.bet_size * 2)
			else:
				self.capital -= self.bet_size

			self.lose = (self.capital < self.min_betsize)

	def reset(self):
		self.hands = [Hand()]

	def action(self, hand, dealer_card, count):
		return self.strategy.action(hand.cards, dealer_card, count)

	def insure(self, hand, dealer_card, count):
		return self.strategy.insure(hand.cards, dealer_card, count)


class Strategy:

	pairs = pd.read_csv("pairs.csv")
	pairs.columns = ['', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'A']
	pairs.index = ['22', '33', '44', '55', '66', '77', '88', '99', 'TT', 'AA']
	
	soft = pd.read_csv("soft.csv")
	soft.columns = ['', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'A']
	soft.index = ['A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'AT']
	
	hit = pd.read_csv("hit.csv")
	hit.columns = ['', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'A']
	hit.index = ['4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21']


	def __init__(self, scores, min_betsize):
		self.scores = scores
		self.min_betsize = min_betsize

	def change_betsize(self, betsize):
		self.min_betsize = betsize

	def bet(self, count, num_cards):
		true_count = (count // ((num_cards // 52)+1))
		bet_size = min(max((true_count-1)*self.min_betsize, 10), 200) # 10 IS MINBETSIZE when count <= 1
		return bet_size, true_count

	def action(self, player_cards, dealer_card, count):

		score = 0
		for card in player_cards:
			score += self.scores[card]

		if score > 21:
			return "stay"

		elif (len(player_cards) == 2) and (player_cards[0] == player_cards[1]):
			return self.pairs.loc[str(player_cards[0])*2, dealer_card]

		elif 'A' in player_cards:
			score -= 1
			if score < 10:
				return self.soft.loc['A'+str(score), dealer_card]
			elif score == 10:
				return self.soft.loc['AT', dealer_card]
			elif (score+1) <= 21:
				if (score+1) == 12:
					if (dealer_card == '2') and (count >= 3):
						return "stay"
					elif (dealer_card == '3') and (count >= 1.5):
						return "stay"
					elif (dealer_card == '4') and (count >= 0):
						return "hit"
					elif (dealer_card == '5') and (count >= -2):
						return "hit"
					elif (dealer_card == '6') and (count >= -1):
						return "hit"
				elif (score+1) == 13:
					if (dealer_card == '2') and (count >= -1):
						return "hit"
					elif (dealer_card == '3') and (count >= -2):
						return "hit"
				elif (score+1) == 9:
					if (dealer_card == '2') and (count >= 1.5):
						return "double"
					elif (dealer_card == '7') and (count >= 5):
						return "double"
				elif (score+1) == 10:
					if (dealer_card == 'T') and (count >= 7):
						return "double"
					elif (dealer_card == 'A') and (count >= 5):
						return "double"
				elif (score+1) == 11:
					if (dealer_card == 'A') and (count >= 2):
						return "double"

				return self.hit.loc[str(score+1), dealer_card]
			else:
				return "stay"

		elif (score) <= 21:
			if (score) == 12:
				if (dealer_card == '2') and (count >= 3):
					return "stay"
				elif (dealer_card == '3') and (count >= 1.5):
					return "stay"
				elif (dealer_card == '4') and (count >= 0):
					return "hit"
				elif (dealer_card == '5') and (count >= -2):
					return "hit"
				elif (dealer_card == '6') and (count >= -1):
					return "hit"
			elif (score) == 13:
				if (dealer_card == '2') and (count >= -1):
					return "hit"
				elif (dealer_card == '3') and (count >= -2):
					return "hit"
			elif (score) == 9:
				if (dealer_card == '2') and (count >= 1.5):
						return "double"
				elif (dealer_card == '7') and (count >= 5):
					return "double"
			elif (score) == 10:
				if (dealer_card == 'T') and (count >= 7):
					return "double"
				elif (dealer_card == 'A') and (count >= 5):
					return "double"
			elif (score) == 11:
				if (dealer_card == 'A') and (count >= 2):
					return "double"
			return self.hit.loc[str(score), dealer_card]

	def insure(self, player_cards, dealer_card, count):

		return (dealer_card == 'A') and (count >= 3)


class Game:

	def __init__(self, num_decks=6, pen_rate=0.8, num_hands=1000, capital=10000, min_betsize=10, verbose=False):
		self.num_decks = num_decks
		self.pen_rate = pen_rate
		self.num_hands = num_hands
		self.capital = capital
		self.min_betsize = min_betsize
		self.verbose = verbose

		self.deck = Deck(self.num_decks, self.pen_rate)
		self.dealer = Dealer()
		self.player = Player(self.capital, self.min_betsize)
		
		# self.result = self.simulate()

	def simulate(self):

		capital_path = np.array([self.player.capital])
		for n in range(self.num_hands):
			if (n % 100000) == 0:
				print(n, capital_path[-1])
			# player bets based on count
			self.player.bet(self.deck.count, self.deck.num_cards)
			if self.verbose:
				print("Count: ", self.deck.count, " True count: ", self.player.true_count)
				print("Start Capital: ", capital_path[-1])
				print("Bet Size: ", self.player.bet_size)

			# dealer is dealt 2 cards, one of which is hidden
			self.dealer.add_card(self.deck.deal())
			self.dealer.add_card(self.deck.deal())

			hand = self.player.hands[0]

			# player is dealt 2 cards
			hand.add_card(self.deck.deal())
			hand.add_card(self.deck.deal())
			if self.verbose:
				print("Player Cards: ", hand.cards)
				print("Dealer Cards: ", self.dealer.cards)

			insurance = self.player.insure(hand, self.dealer.cards[-1], self.player.true_count)
			if self.verbose:
				print("Insurance: ", insurance)

			if self.dealer.blackjack: # if dealer gets blackjack
				if insurance:
					self.player.settle(win=True, double=True)

				if hand.blackjack: # if player gets blackjack
					if self.verbose:
						print("Both have Blackjack")
					self.player.settle(win="tie")
				else:
					self.player.settle(win=False)
					if self.verbose:
						print("Dealer has Blackjack")

			elif hand.blackjack: # if player (only) gets blackjack
				#insurance lost
				if insurance:
					self.player.settle(win=False)
				self.player.settle(win=True, blackjack=True)

				if self.verbose:
					print("Player has Blackjack")


			else: # if neither gets blackjack
				#insurance lost
				if insurance:
					self.player.settle(win=False)
				#player's turn
				action = self.player.action(hand, self.dealer.cards[-1], self.player.true_count)
				didhit = False
				while action != "stay":
					if action == "hit":
						didhit = True
						hand.add_card(self.deck.deal())
						if hand.bust:
							if self.verbose:
								print("player bust")
							break

					elif (action == "double"):

						hand.add_card(self.deck.deal())
						hand.double = (not didhit)
						if self.verbose:
							if hand.double:
								print("player double")
							if hand.bust:
								print("player bust")
						break

					elif (action == "split"):
						self.split(idx=0)
						if self.verbose:
							print("Split hand end: ", [h.cards for h in self.player.hands])
						break						

					if self.player.hands[0].bust:
						if self.verbose:
							print("player bust")
						break
					
					action = self.player.action(hand, self.dealer.cards[-1], self.player.true_count)


				if self.verbose:
					print("Player end cards: ", [h.cards for h in self.player.hands])
				#dealer's turn
				if (False in [h.bust for h in self.player.hands]):
					while self.dealer.should_hit():
						self.dealer.add_card(self.deck.deal())
				if self.verbose:
					print("Dealer end cards: ", self.dealer.cards)

				# see who wins
				self.compare()

			# print("player hand: ", [h.cards for h in self.player.hands])
			# print("dealer hand: ", self.dealer.cards)
			# print(self.player.capital)
			capital_path = np.append(capital_path, self.player.capital)
			if self.verbose:
				print("End Capital: ", capital_path[-1])
			if self.deck.num_cards <= self.deck.min_cards:
				self.deck.reshuffle()

			self.player.reset()
			self.dealer.reset()

			if self.player.capital <= self.min_betsize:
				break

			self.player.strategy.change_betsize(self.player.capital//100)

		return capital_path

	def split(self, idx, layer=1):
		
		split_hand = self.player.hands[idx].cards
		hand1, hand2 = Hand(), Hand()
		hand1.add_card(split_hand[0])
		hand1.add_card(self.deck.deal())
		hand2.add_card(split_hand[1])
		hand2.add_card(self.deck.deal())

		# print("split hands: ", hand1.cards, hand2.cards, idx)

		del self.player.hands[idx]
		self.player.hands.insert(idx, hand2)
		self.player.hands.insert(idx, hand1)

		for i, hand in enumerate(self.player.hands[idx:idx+2]):
			if hand.cards[0] != 'A':
				didhit = False
				action = self.player.action(self.player.hands[idx+i], self.dealer.cards[-1], self.player.true_count)
				while action != "stay":
					if action == "hit":
						didhit = True
						self.player.hands[idx+i].add_card(self.deck.deal())
						if self.player.hands[idx+i].bust:
							break

					elif (action == "double"):
						hand.add_card(self.deck.deal())
						hand.double = (not didhit)

					elif (action == "split"): 
						idx = self.split(idx+i, layer=layer+1)
						break

					if self.player.hands[idx+i].bust:
						break

					action = self.player.action(self.player.hands[idx+i], self.dealer.cards[-1], self.player.true_count)

		return idx

	def compare(self):

		if (self.dealer.soft) and (self.dealer.score <= 11):
			self.dealer.score += 10

		for hand in self.player.hands:
			if (hand.soft) and (hand.score <= 11):
				hand.score += 10

			if hand.bust:
				self.player.settle(win=False, double=hand.double)
			elif self.dealer.bust:
				self.player.settle(win=True, double=hand.double, blackjack=hand.blackjack)

			elif hand.score == self.dealer.score:
				self.player.settle(win="tie")
				# print("tie")
			elif hand.score < self.dealer.score:
				self.player.settle(win=False, double=hand.double)
				# print("Dealer wins")
			else:
				self.player.settle(win=True, double=hand.double, blackjack=hand.blackjack)
				# print("Player wins")

		return	


def start(num_hands=1000, num_trials=1, verbose=False):

	res = np.array([])
	if num_trials > 1:
		for i in range(num_trials):
			game = Game(num_hands=num_hands, verbose=verbose)
			n = game.simulate()
			res = np.append(res, n[-1])

		plt.hist(res)
		plt.show()
		return res

	else:
		game = Game(num_hands=num_hands, verbose = verbose)
		n = game.simulate()
		plt.plot(n)
		plt.show()

		return n
