""" Base quiz for Quizzer.

    Author: Alastair Hughes
    Contact: <hobbitalastair at yandex dot com>

"""

from random import randint

# Try to correct python 3/2 differences
import sys
if sys.version_info.major >= 3:
    get_input = input
else:
    print("Running on python 2 or less!")
    get_input = raw_input
    FileNotFoundError = IOError


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


    def __init__(self, quiz=None):
        """ Initialise self """

        # Set the initial quiz state
        self.running = True
        if quiz != None:
            self.quiz = Quiz(quiz)
        else:
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



