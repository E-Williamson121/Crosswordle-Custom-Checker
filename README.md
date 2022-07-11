# Crosswordle-Custom-Checker
This repository contains a python script which allows for checking crosswordle puzzles against the full extended wordlist (compared with guess list as crosswordle's original checker).

The script is relatively customizable. The main function to call being:

solve_function(options, nums, table)

options - the list of words which may be played in the bottom-most row of the grid (bear in mind that solves will be slow for unrestricted puzzles or large lists)

nums - the list of colours (ternary)

table - a lookup table detailing all words which can fit into a row of a given colouring under a solution.

which acts as a front-end to a recursive backtracking solver program.

will return the list of all possible solutions to the puzzle, which may then be further analyzed.
