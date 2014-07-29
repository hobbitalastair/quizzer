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

"""

VERSION=0.1

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox

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

        self.total_questions = 0

        try:
            quiz = open(quiz_file)
        except FileNotFoundError:
            raise QuizException("Quiz file '{}' not found!".format(quiz_file))
        
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

                # Set the new question and answer
                if line.count(':') != 1: # Not a valid line!
                    raise QuizException("Line {} is not a valid line -".format(
                                                                    line_num) + 
                                        " expected a new question " + 
                                        "(question: answer)!")

                question, answer = line.split(':')
                current_question = Question(question.strip(), answer.strip())

            elif current_question != None:
                # On an older question
                # Must be multichoice
                if current_question.sort != 'multichoice':
                    current_question.sort = 'multichoice'
                    current_question.choices = {}

                # Get the added choice
                choice_id, value = line.split(':')
                current_question.choices[choice_id.strip()] = value.strip()

            else:
                raise QuizException("Indented line before the start of " +
                                    " a question!")

        if current_question != None:
            self.questions.append(current_question) # Add in the last question
        else:
            raise QuizException("Quiz file '{}' has no questions!".format(
                                                                   quiz_file))


    def get_question(self):
        """ Return a randomly selected question
            TODO: Add semi-random selection...
        """

        self.total_questions += 1

        # Calculate the total weight
        total_weight = 0
        for question in self.questions:
            total_weight += question.weight(self.total_questions)
        
        rand_value = randint(0, int(total_weight))

        combined_weight = 0
        for question in self.questions:
            weight = question.weight(self.total_questions)
            combined_weight += weight
            if rand_value <= combined_weight:
                return question
            else:
                combined_weight += weight


class QuizException(Exception):
    """ Exception to be raised when an error occurs while parsing a quiz """

    pass


class Question(object):
    """ A question class
        
        This will be generated by the quizzer
    """

    def __init__(self, question, answer, sort='prompt'):
        """ Initialise the Question """

        self.question = question
        self.answer = answer
        self.sort = sort

        self.choices = None

        # Stats for this question...
        self.wrong = 0
        self.correct = 0


    def weight(self, total_question):
        """ Return an integer value - the weight of the current question """

        return 1 + (self.wrong - (self.correct / 2))


""" Actual quizzes """


class BaseQuiz(object):
    """ Base quiz object
    
        This cannot be used on it's own as it has no UI...
    """

    # States that the quiz could be in
    NEW_QUIZ=0      # Wanting a new quiz
    NEW_QUESTION=1  # Asking a new question
    ANSWER=2        # Waiting for an answer
    REVEALING=3     # Showing the answer to the quiz

    
    class StateError(BaseException):
        """ Raised when the quizzes current state is invalid """

        pass


    def __init__(self):
        """ Initialise self """

        # Set the initial quiz state
        self.running = True
        self.quiz = None

        self._answer = None
        self.question = None


    def __str__(self):
        """ Return a string showing what is happening at the moment """

        return "<{} using quiz {}, on question {}>".format(self.__name__, 
                                                           self.quiz,
                                                           self.question)


    def get_state(self):
        """ Returns the current state """

        if self.quiz == None:
            return self.NEW_QUIZ
        elif self.question == None and self.answer == None:
            return self.NEW_QUESTION
        elif self.question != None and self.answer == None:
            return self.ANSWER
        elif self.question != None and self.answer != None:
            return self.REVEALING
        else:
            raise StateError("Quiz {} in unknown state!".format(self))


    # UI properties

    @property
    def answer(self):
        """ Return the current answer to the question """

        return self._answer


    @answer.setter
    def answer(self, answer):
        """ Set the current answer to the question """

        self._answer = answer


    # Quiz commands

    def quit(self):
        """ Quit quizzing """

        self.running = False
        self.quiz = None


    def cancel_quiz(self):
        """ Cancel the current quiz """

        if self.get_state() == self.NEW_QUIZ:
            self.quit()
        else:
            self.quiz = None
            self.new_quiz()


    def quiz_help(self):
        """ Get help for the current state
            Return a string of help for the current state
        """

        return "Help for this state is not implemented"


    def new_quiz(self):
        """ Setup for a new quiz """

        while self.quiz == None and self.running == True:
            self.load_quiz()
        
        if self.quiz != None: # If a quiz was loaded
            self.next_question()


    def next_question(self):
        """ Move onto the next question
        
            This clears the current question and answer
        """

        self.question = None
        self.answer = None

        self.question = self.quiz.get_question()
        self.display_question()


    def accept_answer(self):
        """ Accept the current answer to the problem """

        # Create a user friendly version of the answer
        if self.question.sort == 'multichoice':
            correct_answer = self.question.choices[self.question.answer]
        else:
            correct_answer = self.question.answer

        if self.question.answer == self.answer:
            response = "Answer '{}' was correct!".format(correct_answer)
            self.question.correct += 1
        else:
            response = "Wrong! The correct answer was '{}'!".format(
                                                                correct_answer)
            self.question.wrong += 1

        self.set_answer_response(response)


    # UI related stuff...


    def load_quiz(self):
        """ Get a new quiz from the user and load """

        raise NotImplementedError("BaseQuiz is only a template!")


    def display_question(self):
        """ Display the current question """

        raise NotImplementedError("Base quiz is only a template!")


    def set_answer_response(self, response):
        """ Set the response to the current answer """

        raise NotImplementedError("Base quiz is only a template!")


# Quiz UI


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

        value = input(message + ": ") # Get input

        #TODO: Implement other commands (?)
        if value.lower() == "quit":
            # Quit quizzing
            self.quit()
        elif value.lower() == "help":
            # Get help
            print(self.quiz_help)
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
            print(self.question.question)
        elif sort == 'multichoice':
            print(self.question.question)
            pairs = ["{}: {}".format(choice, self.question.choices[choice])
                     for choice in self.question.choices]
            choices = "    \n".join(pairs)
            print(choices)
        else:
            raise ValueError("Question sort '{}' not recognized!".format(sort))


    def set_answer_response(self, response):
        """ Print out the response to the answer """
        print(response)


class TkQuiz(tk.Frame, BaseQuiz):
    """ Tkinter Quizzer UI """


    def __init__(self, *args, **kargs):
        """ Initialise self """

        # Initialise the quiz side of things
        BaseQuiz.__init__(self, *args, **kargs)

        # Set up the Tk instance
        master = tk.Tk()
        tk.Frame.__init__(self, master)
        self.master.title("Quizzer version {}".format(VERSION))

        self.pack()

        # Create the answer string variable
        self._answer = tk.StringVar()

        # Create the next button's text variable
        self.next_button_text = tk.StringVar()

        # Create the ui
        self.create_ui()

        self.new_quiz() # Start the ball rolling by getting a new quiz


    def run(self):
        """ Run the UI """
        self.master.mainloop()


    def create_ui(self):
        """ Create the quiz ui """

        # Create the buttons
        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(side='bottom')
        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel",
                                        command=self.cancel_quiz)
        cancel_button.pack(side='left')
        # Accept button
        accept_button = ttk.Button(button_frame,
                                        textvariable=self.next_button_text,
                                        command=self.accept)
        self.next_button_text.set("Accept")
        accept_button.pack()

        # Placeholder question UI
        self.question_ui = ttk.Frame(self)


    def accept(self):
        """ Accept and carry on

            This either calls the accept_answer method or the next_question
            method, depending on the current value of self.next_button_text
            It also inverts the current state of the button
        """

        if self.next_button_text.get() == "Accept":
            self.accept_answer()
            self.next_button_text.set("Next")
        elif self.next_button_text.get() == "Next":
            self.next_question()
            self.next_button_text.set("Accept")


    # UI specific properties

    @property
    def answer(self):
        """ Return the current answer """

        if self.question.sort == 'prompt':
            return self.question_choices.get().strip()
        else:
            return self._answer.get()


    @answer.setter
    def answer(self, answer):
        """ Set the current answer to 'answer' """

        self._answer.set(answer)


    """ UI specific shared methods """

    def load_quiz(self):
        """ Load a new quiz to use """

        self.master.withdraw() # Hide the main window

        try:
            self.quiz = Quiz(filedialog.askopenfilename())
        except QuizException as error:
            tk.messagebox.showerror("Quiz error",
               "Quiz could not be loaded because error \
                '{}' occured!".format(error))
        except Exception as error:
            tk.messagebox.showerror("Unknown error",
                          "Unknown error occured:\n{}".format(error))

        self.master.deiconify() # Recreate the main window


    def display_question(self):
        """ Display the current question
        
            Also make sure that the current button text is correct
        """

        # First, clear the current question ui
        self.question_ui.destroy()
        # Create a new frame for the question
        self.question_ui = ttk.Frame(self)

        # Create the main question header
        question = ttk.Label(self.question_ui,
                             text=self.question.question)
        question.pack(side='top')

        # Show the possible choices
        # Setup a new UI depending on question sort
        sort = self.question.sort
        if sort == 'prompt':
            self.question_choices = ttk.Entry(self.question_ui)
        elif sort == 'multichoice':
            # Create the choice roundbutton set
            self.question_choices = ttk.Frame(self.question_ui)
            for choice_id, choice in self.question.choices.items():
                radio = ttk.Radiobutton(self.question_choices,
                                        text=choice,
                                        variable=self._answer,
                                        value=choice_id)
                radio.pack()
        else:
            raise ValueError("Unknown question sort {}!".format(sort))

        # Pack the UI components
        self.question_choices.pack()
        self.question_ui.pack(side='top')


    def set_answer_response(self, answer):
        """ Set the current answer response """

        self.question_ui.destroy()
        self.question_ui = ttk.Label(self, text=answer)
        self.question_ui.pack(side='top')



if __name__ == "__main__":

    #TODO: Fix this hack
    try:
        quiz_ui = TkQuiz()
    except tk._tkinter.TclError:
        quiz_ui = CLIQuiz()
    quiz_ui.run() # Run the quiz

