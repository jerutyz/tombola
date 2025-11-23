def run_simulations(game, n=1000):
    """Corre N simulaciones para cualquier juego que implemente BaseGame."""
    all_draws = [game.draw() for _ in range(n)]

    freq = {}
    for draw in all_draws:
        for num in draw:
            freq[num] = freq.get(num, 0) + 1

    return freq
