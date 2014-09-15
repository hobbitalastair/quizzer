""" Quizzer Tkinter interface.
     
    This is in a different file to the main quizzer application because otherwise, if tkinter cannot be imported, 'tk.Frame' does not exist...

    Author: Alastair Hughes
    Contact: <hobbitalastair at yandex dot com>

"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox

from basequiz import BaseQuiz, \
                     Quiz, \
                     Question, \
                     QuizException

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



