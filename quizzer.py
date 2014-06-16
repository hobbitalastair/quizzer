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

    - Randomization of the order of multichoice questions
    - Psuedo randomization of questions
    - Images
    - Letting sets of possible answers being allocated seperatly from questions
    - Adding more question types
    - CLI argparsing
    - Framebuffer UI

    Author: Alastair Hughes
    Contact: <hobbitalastair@gmail.com>

    Changelog:

    10-6-2014

    Started!

    11-6-2014

    Started on parsing quiz files

    12-6-2014

    Moved the main control and flow logic into a BaseQuiz object

"""

VERSION=0.1

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from random import randint


class Quiz(object):
    """ A quiz
    
        Quiz file format:

        <file_segment> ::= <comments> | <question> | <blank line>
        
        Quiz question format:
        
        <actual question>: <answer>
            [<choice title>: <choice>]
            [...]

    """

    def __init__(self, quiz_file):
        """ Initialise self using quiz_file, and load the quiz """

        try:
            quiz = open(quiz_file)
        except FileNotFoundError:
            raise ValueError("Quiz file '{}' not found!".format(quiz_file))
        
        # Parse the file...

        # Get the lines and close the file
        lines = quiz.readlines()
        quiz.close()

        # Convert lines to a dict in format line number: line
        quiz_lines = {}
        for index, line in enumerate(lines):
            # Ignore blank lines and commented lines
            #TODO: Add support for continued lines
            if len(line.strip()) != 0 and line[0] != '#':
                quiz_lines[index] = line

        # Questions!
        self.questions = []
        current_question = None

        for line_num in quiz_lines:
            line = quiz_lines[line_num]
            if line[:4] != '    ':
                #TODO: Check question for validity
                    
                # Save the old question
                if current_question != None:
                    self.questions.append(current_question)

                # Clear the current question
                current_question = {}
                # Set the new question and answer
                question, answer = line.split(':')
                current_question['question'] = question.strip()
                current_question['answer'] = answer.strip()
                current_question['type'] = 'prompt'

            elif current_question != None:
                # On an older question
                # Must be multichoice
                if current_question['type'] != 'multichoice':
                    current_question['type'] = 'multichoice'
                    current_question['choices'] = {}

                # Get the added choice
                choice_id, value = line.split(':')
                current_question['choices'][choice_id.strip()] = value.strip()

            else:
                raise QuizException("Indented line before the start of " +
                                    " a question!")

        self.questions.append(current_question) # Add in the last question...


    def get_question(self):
        """ Return a randomly selected question
            TODO: Add semi-random selection...
        """

        return self.questions[randint(0, len(self.questions) - 1)]


class QuizException(Exception):
    """ Exception to be raised when an error occurs while parsing a quiz """

    pass


class BaseQuiz(object):
    """ Base quiz object
    
        This cannot be used on it's own as it has no UI...
    """


    def __init__(self):
        """ Initialise self """

        # Set the initial quiz state
        self.running = True
        self.quiz = None

        self.question = None
        self.answer = None


#    def run(self):
        """ Run a quiz """



        # Get the initial quiz
        while self.running and self.quiz == None:
            self.new_quiz()

        # Run if there is a quiz to run and the user has not quit
        while self.running and self.quiz != None:
            # Run the quiz, getting a new one if required

            # Get the first question of the quiz
            question = self.quiz.get_question()

            # Ask the quiz questions
            while self.quiz != None:
                
                # Ask the question
                if question['type'] == 'prompt':
                    answer = self.prompt(question['question'])
                elif question['type'] == 'multichoice':
                    answer = self.multichoice(question['question'],
                                              question['choices'])
                else:
                    # Unknown question type
                    self.notify("Questions of type {} are not supported!".format(question['type']))
                    answer = None
                    question = self.quiz.get_question() # Load a new question

                # Check answer
                if answer != None: # Will be none if a command was entered
                    if answer == question['answer']:
                        self.notify("That was the correct answer!")
                    else:
                        self.notify("Wrong answer! Correct answer: {}".format(
                                                           question['answer']))

                    # The question has been answered; load a new question
                    question = self.quiz.get_question()
                
            if self.running:
                # Load a new quiz if still active
                self.new_quiz()


    def quit(self):
        """ Quit quizzing """

        self.running = False
        self.quiz = None


    def cancel(self):
        """ Cancel the current quiz """

        self.quiz = None


    def accept(self):
        """ Submit the current answer """

        raise NotImplementedError()


    def next(self):
        """ Move onto the next question """

        raise NotImplementedError()


    def new_quiz(self):
        """ Set the quiz object """

        is_valid = False

        while not is_valid and self.running:
            quiz_name = self.get_file("New quiz")
            if quiz_name != None:
                try:
                    quiz = Quiz(quiz_name)
                except ValueError:
                    self.notify("Invalid quiz {}! File does not exist".format(
                                                                    quiz_name))
                else:
                    is_valid = True
                    self.quiz = quiz


    def prompt(self, message):
        """ Return the value of the prompt """
        print("prompt({})".format(message))
        return ""


    def multichoice(self, question, choices):
        """ Return a user inputter reply to a multichoice question """
        print("multichoice({}, {})".format(question, choices))
        return ""


    def notify(self, message):
        """ Output to the user a message """
        print("message({})".format(message))


    def set_file(self, message):
        """ Get the user to select a file to open """
        return self.prompt(message)


class CLIQuiz(BaseQuiz):
    """ CLI test quizzer
    
        Features to add:

        - Tab completion
        - Pictures replaced with ascii art
        - Better multichoice:
          - Randomly order the possible answers
          - Replace the question id with A/B/...
    """


    def prompt(self, message):
        """ Return the value of the prompt """

        value = input(message + ": ")
        #TODO: Implement other commands (?)
        if value.lower() == "quit":
            self.quit() # Quit
            return None
        elif value.lower() == "help":
            self.notify("Help is not yet implemented")
            return None
        elif value.lower() == "cancel":
            self.cancel()
            return None
        else:
            return value


    def multichoice(self, question, choices):
        """ Return a user inputter reply to a multichoice question """

        prompt = question
        for choice_id in choices:
            prompt += "\n    " + choice_id + ": " + choices[choice_id]

        prompt += "\nAnswer"

        return self.prompt(prompt)


    def notify(self, message):
        """ Output to the user a message """
        print(message)


class TkQuiz(tk.Frame, BaseQuiz):
    """ Tkinter Quizzer UI """


    def __init__(self, *args, **kargs):
        """ Initialise self """

        master = tk.Tk()
        tk.Frame.__init__(self, master)
        self.master.title("Quizzer version {}".format(VERSION))

        self.pack()
        self.create_ui()
        self.pack_ui()

        BaseQuiz.__init__(self, *args, **kargs)


    def create_ui(self):
        """ Create the quiz ui """

        # Create the two UI frames
        self.button_frame = tk.Frame(self)
        self.question_frame = tk.Frame(self)

        # Create the buttons in the button frame
        self.cancel_button = ttk.Button(self, text="Cancel",
                                        command=self.cancel)
        self.accept_button = ttk.Button(self, text="Accept",
                                        command=self.accept)


    def pack_ui(self):
        """ Pack the quiz ui """

        # Pack the frames
        self.button_frame.pack(side="bottom")
        self.question_frame.pack(side="top")

        # Pack the buttons
        self.cancel_button.pack(side="left")
        self.accept_button.pack(side="right")


    def notify(self, message):
        """ Give a message to the user """

        raise NotImplementedError("This is not yet implemented")


    def prompt(self, message):
        """ Prompt the user with message for some input """

        raise NotImplementedError("This is not yet implemented")


    def multichoice(self, question, choices):
        """ Prompt for a multichoice question """

        raise NotImplementedError("This is not yet implemented")


    def get_file(self, message):
        """ Return a filepath, prompting with message """

        return filedialog.askopenfilename()


if __name__ == "__main__":

    quiz_ui = TkQuiz() # TODO: Add options to use one or the other
    quiz_ui.run() # Run the quiz

