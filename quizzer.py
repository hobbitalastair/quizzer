#!/usr/bin/env python
""" A quizzer/flashcard style Tkinter program in python

    Designed for my drivers licence practice ;)

    A quiz runs like so:

    While running:
    - Prompts for a quiz to run
    - Parses and builds a quiz object
    - While quizzing:
      - Gets a question from the quiz
      - Checks the answer
      - Responds

    Features to add:

    - Randomising the question letters and orders so that each question has a
      different letter each time, a different order, and the letters are always
      ordered.
    - Psuedo randomization of questions - done?
    - Images
    - Letting sets of possible answers being allocated seperatly from questions
    - Adding more question types
    - Framebuffer UI
    - Checking that the given answer is valid for multichoice questions

    Author: Alastair Hughes
    Contact: <hobbitalastair at yandex dot com>

    Changelog:

    10-6-2014

    Started!

    11-6-2014

    Started on parsing quiz files

    12-6-2014

    Moved the main control and flow logic into a BaseQuiz object

    17-6-2014

    Moved to a state based system for the CLI UI to allow universal event based
    programming

    21-6-2014

    Adjusted so that the Tk UI works, and moved some of the UI specific stuff
    into properties

    8-9-2014

    Moved the tk quiz part to another file to allow avoiding tk

    19-8-2015

    Added a help function and misc bug fixes/cleanups.

    28-10-2015

    Added some extra randomisation of the order of multichoice questions.
    Added some colour to the CLI.

"""

VERSION=0.1

# Try to import a tk quizzer
try:
    from tkquiz import TkQuiz
except ImportError:
    # Failed to import tk!
    # This is so that the program falls back to the CLI interface
    TkQuiz = None

# Try to correct python 3/2 differences
import sys
if sys.version_info.major >= 3:
    get_input = input
else:
    get_input = raw_input

from random import shuffle

# For CLI argument support
import argparse

# Quizzer stuff
from basequiz import BaseQuiz, \
                     Quiz, \
                     Question, \
                     QuizException

# Define some colours (this is probably not portable...)
RESET   = '\033[0m'
BOLD    = '\033[1m'
UNDER   = '\033[4m'
REVERSE = '\033[7m'
BLANK   = '\033[8m'
RESET   = '\033[0m'
GREY    = '\033[90m'
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
BLUE    = '\033[94m'
PINK    = '\033[95m'
CYAN    = '\033[96m'
WHITE   = '\033[97m'

WRONG   = BOLD + RED
RIGHT   = BOLD + GREEN
HIGH    = CYAN
PROMPT  = WHITE


class CLIQuiz(BaseQuiz):
    """ CLI test quizzer
    
        Features to add:

        - Tab completion
        - Pictures replaced with ascii art
        - Better multichoice:
          - Randomly order the possible answers
          - Replace the question id with A/B/...
    """

    
    # CLI control functions
               

    def run(self):
        """ Run the quizzer
        
            This involves getting the state and acting as required
        """

        while self.running:
            state = self.get_state()
            
            # Get the prompt for the current state
            if state == self.NEW_QUESTION:
                self.next_question()
            elif state == self.REVEALING:
                self.accept_answer()
                self.next_question()
            elif state == self.NEW_QUIZ:
                self.new_quiz()
            elif state == self.ANSWER:
                # Get user input and continue
                user_input = self.prompt("Answer")
                if user_input != None:
                    # Collect an answer
                    self.answer = user_input
            else:
                raise NotImplementedError(
                          "{} does not support a state of {}".format(self,
                                                                     state))


    def prompt(self, message):
        """ Return the value of the prompt """

        result = None # Result

        value = get_input(message + ": ") # Get input

        #TODO: Implement other commands (?)
        if value.lower() == "quit":
            # Quit quizzing
            self.quit()
        elif value.lower() == "help":
            # Get help
            self.quiz_help()
        elif value.lower() == "cancel":
            # Cancel!
            self.cancel_quiz()
        else:   # Return the user input
            result = value

        return result

    
    # UI properties
 

    @property
    def answer(self):
        """ Return the current answer """

        return self._answer


    @answer.setter
    def answer(self, value):
        """ Set the current answer to 'value' """

        self._answer = value


    # UI specific functions


    def quiz_help(self):
        """ Print out the quiz help """
        
        print("""
Oh dear! Obviously I need to improve the UI so that it is more intuitive...

Commands:
"""+HIGH+"quit"+RESET+"""    - exit the quiz.
"""+HIGH+"cancel"+RESET+"""  - cancel the current quiz.
"""+HIGH+"help"+RESET+"""    - print this message.
""")


    def load_quiz(self):
        """ Load a new quiz from the user """

        user_input = self.prompt("New quiz")

        if user_input != None:
            try:
                self.quiz = Quiz(user_input)
            except QuizException as error:
                print("Quiz '{}' not loaded due to {}!".format(
                                               user_input, error))
            else:
                print("Quiz {} loaded".format(user_input))
        else:
            return None


    def display_question(self):
        """ Display the question currently loaded """

        sort = self.question.sort

        if sort == 'prompt':
            print(PROMPT+self.question.question+RESET)
        elif sort == 'multichoice':
            print(PROMPT+self.question.question+RESET)
            pairs = [HIGH + "{}:".format(choice) + RESET \
                    + " {}".format(self.question.choices[choice])
                     for choice in self.question.choices]
            shuffle(pairs)
            choices = "    \n".join(pairs)
            print(choices)
        else:
            raise ValueError("Question sort '{}' not recognized!".format(sort))


    def set_answer_response(self, correct_answer, correct):
        """ Print out the response to the answer """

        if correct:
            print(("Answer '{}' was "+RIGHT+"correct!"+RESET).format(
                        correct_answer))
        else:
            print((WRONG+"Wrong!"+RESET+" The correct answer was '{}'.").format(
                correct_answer))


def cli(tk):
    """ Handle the CLI interface to Quizzer """

    parser = argparse.ArgumentParser(usage="quizzer application, written in python")

    parser.add_argument("--interface", default="cli", help="One of tk, or cli")
    parser.add_argument("--quiz", default=None, help="Quiz file to load")

    args = parser.parse_args()

    interface = args.interface

    if interface == "tk":
        if tk == None:
            parser.error("tk cannot be imported!")
        try:
            quiz_ui = TkQuiz(args.quiz)
        except tk._tkinter.TclError:
            print("No X detected; falling back to a CLI quiz!")
            interface = "cli"
    if interface == "cli":
        quiz_ui = CLIQuiz(args.quiz)
    else:
        parser.error("Unknown interface: {}".format(interface))

    quiz_ui.run()


if __name__ == "__main__":
    # Call the CLI function
    cli(TkQuiz)

