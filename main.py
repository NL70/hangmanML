from model import MainModel, ModelConfig
from dataloader import Word, MAX_WORD_LEN, MIN_WORD_LEN
import matplotlib.pyplot as plt
import statistics
from tqdm import tqdm
import time

weights_path = './prev/v2.1-1k-200.pth'

config = ModelConfig()
model = MainModel(config, weights_path)

def solve_hangman(target_word: str, verbose=False):
    assert len(target_word) <= MAX_WORD_LEN, len(target_word) >= MIN_WORD_LEN
    word = Word('_' * len(target_word))
    prev_guesses = [0]*26
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
            print(f'Guess: {chr(output+97)}')
        
        prev_guesses[output] = 1
        num_tries += 1
        
    return num_tries, time.time() - start_time
        
def test_loop(filename, repeats=3):
    num_tries = []
    total_time = 0
    total_count = 0
    
    with open(filename) as f:
        raw_words = [word.strip() for word in f.read().splitlines()]
        
        for word in tqdm(raw_words[::10]):
            if len(word) < MIN_WORD_LEN or len(word) > MAX_WORD_LEN:
                continue
            
            total_tries = 0
            for _ in range(repeats):
                tries, time_taken = solve_hangman(word)
                total_tries += tries
                total_time += time_taken
                total_count += 1

            num_tries.append(round(total_tries / repeats, 2))
            
        
    print(f'Time Taken: {round(total_time, 2)}s')
    print(f'Average inference time: {round(total_time*1000 / total_count, 2)}ms')
    print(f'Mean: {round(statistics.mean(num_tries), 2)}, Median: {statistics.median(num_tries)}')
    
    plt.hist(num_tries, bins=range(27))
    plt.title("Distribution of tries taken")
    plt.show()



def main():
    # FOR TESTING
    # test_loop('./data/10k.txt')
    
    # FOR NORMAL GAMEPLAY:
    target_word = str(input("Give me a word pls: ")).strip()
    assert (len(target_word) <= MAX_WORD_LEN or len(target_word) >= MIN_WORD_LEN), "Invalid word length"
        
    num_tries = solve_hangman(target_word, verbose=True)
    print(f'Number of tries: {num_tries[0]}, Time Taken: {round(num_tries[1]*40, 2)}ms')
    
if __name__ == "__main__":
    main()