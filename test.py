from model import MainModel, ModelConfig
from dataloader import Word, MAX_WORD_LEN, MIN_WORD_LEN, device
import matplotlib.pyplot as plt
import statistics
from tqdm import tqdm
import time
import random
import pandas as pd


def solve_hangman(model, target_word: str, verbose=False):
    if not (MAX_WORD_LEN >= len(target_word) >= MIN_WORD_LEN):
        print(f'{target_word} is of invalid length')
        return 0, 0
    word = Word('_' * len(target_word))
    prev_guesses = [0] * 26
    num_tries = 0
    start_time = time.time()

    while True:
        word.string = ''
        for letter in target_word:
            if prev_guesses[ord(letter) - 97]:
                word.string += letter
            else:
                word.string += '_'
        if verbose:
            print(word.string, end='    ')

        if word.string == target_word:
            if verbose:
                print(f'\nTries taken: {num_tries}')
            break

        output = model.infer(word.encode(), word.length, prev_guesses)
        if verbose:
            print(f'Guess: {chr(output + 97)}')

        prev_guesses[output] = 1
        num_tries += 1

    num_fails = num_tries - Word(target_word).num_letters

    return num_tries, time.time() - start_time, num_fails


def test_loop(model, filename, fig_path, num_samples, repeats=3):
    num_tries = []
    words = []
    total_time = 0
    total_count = 0

    with open(filename) as f:
        raw_words = [word.strip() for word in f.read().splitlines()]

        for word in tqdm(random.sample(raw_words, num_samples)):
            if len(word) < MIN_WORD_LEN or len(word) > MAX_WORD_LEN:
                continue

            total_tries = 0
            for _ in range(repeats):
                tries, time_taken = solve_hangman(model, word)
                total_tries += tries
                total_time += time_taken
                total_count += 1

            num_tries.append(round(total_tries / repeats, 2))
            words.append(word)

    df = pd.DataFrame({'Word': words, 'num_tries': num_tries})
    df.to_csv(f'test-results/{fig_path}.csv', index=False)

    print(f'Time Taken: {round(total_time, 2)}s')
    print(f'Average inference time: {round(total_time * 1000 / total_count, 2)}ms')
    print(f'Mean: {round(statistics.mean(num_tries), 2)}, Median: {statistics.median(num_tries)}')

    plt.hist(num_tries, bins=range(27))
    plt.title(f"Distribution of tries taken, Model: {fig_path}")
    plt.savefig(f'test-results/{fig_path}.png')
    plt.show()


def play_game(model):
    target_word = str(input("\nGive me a word pls: ")).strip()
    assert (len(target_word) <= MAX_WORD_LEN or len(target_word) >= MIN_WORD_LEN), "Invalid word length"

    num_tries = solve_hangman(model, target_word, verbose=True)
    print(
        f'Number of tries: {num_tries[0]}, Number of fails: {num_tries[2]}\nTime Taken: {round(num_tries[1] * 40, 2)}ms')


hangman_states = [
    '''
  +---+
      |
      |
      |
      |
      |
=========
''',
    '''
  +---+
  |   |
      |
      |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
      |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\\\  |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\\\  |
 /    |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\\\  |
 / \\\  |
      |
=========
''']


def play_stepwise(model):
    print(hangman_states[0])
    print("""
I am an AI hangman bot!
Lets see if I can guess your word
Sorry if I fail from time to time, I don't know every english word :(
Think of a word (5+ letters pls)...
    """)

    while True:
        wordleninput = input("How long is the word? ")
        if wordleninput.isdigit():
            if int(wordleninput) >= MIN_WORD_LEN:
                if int(wordleninput) <= MAX_WORD_LEN:
                    wordlen = int(wordleninput)
                    break
                else:
                    print(f"Word length should be {MAX_WORD_LEN} or less")
            else:
                print(f"Word length should be {MIN_WORD_LEN} or more")
        else:
            print("Invalid input - enter a number")
    print('\n')
    word = Word('_' * wordlen)
    prev_guesses = [0] * 26

    num_tries = 0
    num_fails = 0

    for letter in word.string:
        print(letter, ' ', end='')
    print('')
    for i in range(wordlen):
        print(i, ' ', end='')

    while True:
        output = model.infer(word.encode(), word.length, prev_guesses)
        print(f'\nMY GUESS: {chr(output + 97)}')

        prev_guesses[output] = 1
        num_tries += 1

        print(
            f"Tell me the positions of the present {chr(output + 97)}'s \n(space-separated numbers, leave empty if not present)")
        while True:
            positions = input("> ").split()
            isValid = True
            for i in positions:
                if not i.isdigit():
                    isValid = False
            if (isValid):
                break

        correct = len(positions) > 0

        if correct:
            for i in positions:
                if (not i.isnumeric) or int(i) >= wordlen or int(i) < 0:
                    print(f"Invalid position {i}")
                    input("Restart?")
                    return
                word.set_letter(int(i), chr(output + 97))

            if word.is_complete():
                break
        else:
            num_fails += 1
            print(hangman_states[min(num_fails, 7)])
            if num_fails == 7:
                print("I LOST!")
                print("But we can still keep going until I get it correct :D ")

        print('\n')
        for letter in word.string:
            print(letter, ' ', end='')
        print('')
        for i in range(wordlen):
            print(i, ' ', end='')

    print(f"\nSolved {word.string} in {num_tries} steps, with {num_fails} fails.\n\n")


def main():
    version = 'v2.4'
    dataset = '20k'
    num_epochs = 500
    weights_path = f'prev/{version}-{dataset}-{num_epochs}.pth'

    config = ModelConfig(version=version)
    model = MainModel(config, weights_path).to(device)
    model.eval()

    # FOR STEPWISE GAMEPLAY
    while True:
        play_stepwise(model)

    # FOR FAST-FORWARDED GAMEPLAY:
    # while True:
    #     play_game(model)

    # FOR TESTING
    # test_loop(model=model, 
    #           filename=f'data/{dataset}.txt', 
    #           fig_path=f'{version}-{dataset}-{num_epochs}', 
    #           num_samples=1000,
    #           repeats=3)


if __name__ == "__main__":
    main()
