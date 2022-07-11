"""
RECURSIVE CROSSWORDLE SOLVER:

This program is a solver for puzzles at crosswordle.vercel.app.

Designed to be a pythonic extension to the official crosswordle (V1) checker - the ability to force tile values will be added later as it is a V2 feature,
it contains all of the same behaviours, but, as a separate python project, allows for finer-controlled customization.

example customizations include:
   using the full word list instead of the official crosswordle checker's list of common words.
   obtaining an array containing all solutions rather than crosswordle's single solutions selected at random
   using the list of colourings to specify a puzzle of a length which the crosswordle checker will not allow (e.g.: 2 rows or >6 rows)

Execution for the solver occurs in two main steps, approximately as follows:

1. Generate colour hash table (or load it from an external file)

The hash table is in the form:
table[(solution, colouring)] = [guesses that can give that colouring]

Using this table serves as a way of skipping having to loop over the wordlist when checking colour possibilities.

2. Recursive backtracker

The solver runs as a recursive backtracking algorithm.

The inputs are the set of colours for the entire puzzle and the possible initial conditions (inputs for the bottom row of the puzzle).

From these, the backtracker repeatedly extends the puzzle by one row, obtaining all options for such an extension as initial conditions for the next row.

The process of extension goes as follows:
Use the lookup table to find words that may fill the colouring for the next row up. These are then filtered via the rules:
     i) A letter which has appeared on a grey tile in a previous row cannot reappear on a grey tile in this row.
     ii) A letter which appears on a yellow *or* grey tile cannot be above a location where it was placed in a previous row.
     iii) The yellows and greens in this row must be a sublist (i.e.: sequence of items chosen from) the yellows and greens in the previous row.
"""

# imports for the program
import random, pickle, os

# NYT wordle answer list ("common words")
with open("wordles.txt") as f:
    WORDLES = f.read().split(", ")

# NYT wordle guess list (any word you can enter into a crosswordle row will be in here)
with open("extendedwordles.txt") as f:
    EXTENDED_WORDLE = f.read().split(", ")

# ====================================== BASIC SCRIPTS ===================================== #
# this part of the code is a few basic scripts that are common for any form of wordle variant search.

# utility function for converting a ternary list, e.g. [2, 2, 1, 2, 0], to a decimal number e.g. 231.
def ternarytonum(t):
    num = 0
    for power, n in enumerate(t[::-1]):
        num += n*(3**power)
    return num

# utility function for converting a decimal number e.g. 134 to a ternary list e.g. [1, 1, 2, 2, 2].
def numtoternary(x):
    nums = []
    while x > 0:
        x, r = divmod(x, 3)
        nums.append(r)
    while len(nums) < 5: nums.append(0)
    return nums[::-1]

# function for generating a hash table allowing O(1) lookup of all words that satisfy a given colouring under a given solution
def get_table(words, ext_words):
    table = {}
    for i, sol in enumerate(ext_words):
        if i % 100 == 0: print(i) # this print statement is so a person using the program knows it's not just hanging.
        for guess in ext_words:
            if sol != guess:
                # get the decimal representation of the (ternary) wordle colouring.
                coln = ternarytonum(wordle_colour(guess, sol))
                # store in the format table[(sol, coln)] = [list of guess words that would work] 
                if (sol, coln) in table.keys():
                    table[(sol, coln)].append(guess)
                else:
                    table[(sol, coln)] = [guess]
    return table

# function for getting the (ternary) wordle colouring of a guess under a given solution.
# Green = 2, Yellow = 1, Grey = 0.
def wordle_colour(guess, solution):
    col = [0, 0, 0, 0, 0]
    observed = []
    for pos, letter in enumerate(solution):
        if guess[pos] == solution[pos]:
            col[pos] = 2
        else: observed.append(letter)

    for pos, letter in enumerate(guess):
        if letter in observed and col[pos] != 2:
            observed.remove(letter)
            if solution[pos] != letter:
                col[pos] = 1

    return col
     
   
# utility function for saving a hashtable to a local file (done via pickling)
def save_hashtable(table, filename):
    with open(filename, 'wb') as fp:
        pickle.dump(table, fp, protocol=pickle.HIGHEST_PROTOCOL)

# utility function for loading hashtables from a local file
def load_hashtable(filename):
    with open(filename, "rb") as fp:
        return pickle.load(fp)


# ================================ RECURSIVE BACKTRACKER ================================== #
# this part of the code details the main implementation of the recursive backtracker program

# input for the recursive backtracker solve:
def solve_function(options, nums, table):
    return recursive_backtracker([], options, nums, table)

# recursive backtracker
def recursive_backtracker(selected, options, nums, table):
    solutions = []
    percent = 0
    if len(selected) == (len(nums)-1) and len(options) > 0:
        for option in options:
            solution = selected + [option]
            solutions.append(solution)
        return solutions
    for i, word in enumerate(options):
        if len(selected) == 0:
            if int(i*100/len(options)) > percent:
                # visual information to relay how the solve is going to the user. you may remove this if you wish.
                percent = int(i*100/len(options))
                print(f"{percent}% complete")
        new_options = extend_puzzle(selected+[word], nums, table)
        res = recursive_backtracker(selected+[word], new_options, nums, table)
        if res != None: solutions += res
    if solutions != []:
        if len(selected) == 0: print(f"{len(solutions)} solutions found.")
        return solutions

# ==================================== PUZZLE EXTENSION ==================================== #
# this part of the code is a collection of functions used to extend puzzles by one row

# extends a puzzle by one row (given previous words, puzzle colours, hash table)
def extend_puzzle(prevwords, nums, table):
    coln = nums[len(prevwords)]
    # step 2: determine which letters have been used as greys in previous guesses.
    greys = get_greys(prevwords, nums)
    # step 3: for each colouring which would be allowed, search for words which would be playable.
    extwords = filter_colour(coln, greys, prevwords, nums, table)
    return extwords

# function for filtering the possible words for a given colour to find words which are playable in that position.
# takes the colour, previous words, previous colourings, hash table, and a list of previously played grey letters.
def filter_colour(coln, greys, words, nums, table):
    sol = words[0]
    prevcoln = nums[len(words) - 1]
    filtered = []
    if (sol, coln) in table.keys():
        # get the list of words which can be played with this colouring under the solution for further filtering.
        fwords = table[(sol, coln)]
        col = numtoternary(coln)
        
        for word in fwords:
            # for each word in the filterable words, check if it satisfies requirements that will allow it to be played on the next row.
            if is_good_word(word, col, greys, words, words[::-1][0], prevcoln):
                filtered.append(word)
    return filtered

# function for checking if a word satisfies requirements to be playable on the next row in crosswordle,
# given that row's colour, the greys from all previous rows, the words from previous rows, and the previous word and previous word's colouring.
# if a word satisfies all requirements, return True, otherwise return False.
def is_good_word(word, col, greys, words, prevword, prevcoln):
    nongreys = []
    for index, letter in enumerate(word):
        if col[index] == 0:
            if letter in greys:
                # rule 1: A letter which has already been used as a grey tile in a previous row cannot be reused as a grey tile in this row.
                return False
            if aligned(letter, index, words):
                # rule 2: letters on yellow or grey tiles cannot appear above somewhere that they were placed in a previous row.
                return False
        else:
            nongreys.append(letter)
            if col[index] == 1 and aligned(letter, index, words):
                # rule 2: letters on yellow or grey tiles cannot appear above somewhere that they were placed in a previous row.
                return False
    
    prevnongreys = get_nongreys(prevword, prevcoln)

    # rule 3: yellow and green letters in this row must be a sublist of the yellow and green letters from the previous row.
    if not is_sublist(nongreys, prevnongreys):
        return False

    return True

# utility function for getting the list of all grey letters from previous guesses.
def get_greys(words, nums):
    greys = []
    for word, coln in zip(words, nums):
        for index, letter in enumerate(word):
            col = numtoternary(coln)
            # any letter on a grey tile is added to the list of grey letters.
            # (note that this includes tiles which are otherwise green/yellow,
            #  the inclusion of such letters corresponds to losing the ability to over-use the letter) 
            if col[index] == 0:
                if not letter in greys:
                    greys.append(letter)
    return greys

# utility function to check whether a letter has appeared in a given spot in any previous word.
# returns true if it has, false otherwise.
def aligned(letter, index, words):
    for word in words:
        if word[index] == letter:
            return True

    return False

# utility function for checking whether an array (sub) is a sublist of a larger array (full)
# a sublist is an array which could be constructed by removing elements from the larger array.
# e.g.: [1,2,2] is a sublist of [2,3,1,3,5,6,2], but not a sublist of [2,3,1,3,5,6] (as in that case, the 2nd 2 is missing).
def is_sublist(sub, full):
    for e in sub:
        if e in full:
            full.remove(e)
        else:
            return False
    return True

# utility function for getting all green and yellow letters from a word, given its colouring.
def get_nongreys(word, coln):
    nongreys = []
    col = numtoternary(coln)
    for index, letter in enumerate(word):
        if col[index] != 0:
            nongreys.append(letter)
    return nongreys

# ======================================== EXECUTION ======================================= #
# a simple example script which executes when this file is loaded.

if __name__ == "__main__":
    if os.path.exists("crosswordle_hashtable.p"):
        print("loading hash table from file")
        table = load_hashtable("crosswordle_hashtable.p")
    else:
        print("generating hash table")
        table = get_table(WORDLES, EXTENDED_WORDLE)
        print("save hashtable to local file to skip generation next time (y/n)?")
        print("(only do this if you have disk space, the file will be BIG!)")
        input()
        if k == "y":
            print("saving hash table to local file")
            save_hashtable(table, "crosswordle_hashtable.p")

    print("solving the example crosswordle at https://crosswordle.vercel.app/?puzzle=v2-0,9,99,20,74,242-x,x,x,x,x,2x")
    sols = solve_function(list(filter(lambda word: word[2] == "x", EXTENDED_WORDLE)), [242,74,20,99,9,0], table)
