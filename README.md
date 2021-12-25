# poker-bot
Creating a CFR Poker Bot in Python to win some $$

## Project Details:
The Poker Bot will be built to play No Limit Hold 'Em poker.
It should be able to play optimally in heads-up poker (according to game theory), and be pretty damn good at full-table too.

## Strategy:
1. Create a custom poker environment (or maybe find another one on GitHub)
2. Learn about counterfactual regret minimization (CFR)
3. Create a bot based that uses CFR to play poker
4. Test with heads-up poker (where CFR achieves Nash equilibrium)
5. Test with full-table poker, and modify accordingly

## Resources:
- [Brown, N. and Sandholm, T., 2017, March. Safe and nested endgame solving for imperfect-information games. In Workshops at the thirty-first AAAI conference on artificial intelligence.](https://proceedings.neurips.cc/paper/2017/file/7fe1f8abaad094e0b5cb1b01d712f708-Paper.pdf)
- [Brown, N., Lerer, A., Gross, S. and Sandholm, T., 2019, May. Deep counterfactual regret minimization. In International conference on machine learning (pp. 793-802). PMLR.](https://arxiv.org/pdf/1811.00164.pdf)
- [Zinkevich, M., Johanson, M., Bowling, M. and Piccione, C., 2007. Regret minimization in games with incomplete information. Advances in neural information processing systems, 20, pp.1729-1736.](https://proceedings.neurips.cc/paper/2007/file/08d98638c6fcd194a4b1e6992063e944-Paper.pdf)
