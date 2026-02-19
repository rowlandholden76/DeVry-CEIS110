class CalculatorError(Exception):
    """Raised when a calculation cannot be performed for logical/mathematical reasons."""
    pass
class HoldenRowlandCalculator:
    # module level variables
    _OPERATORS = ["*","/", "+", "-", "^", "%"]

    def evaluate_expression(self,expr: str) -> str:
        """recursively calculates: sub-expressions inside parenthesis and simple expressions found in the entered 
            expression then replaces the answer of the sub-expression with the answer in the entered expression and 
            calls itself again with the modified expression. This is repeated until there are no more operators left in the expression
            
            Args:
                expr (string): entered expression
            
            Returns:
                string: altered expression and calls itself again until a final result is reached. Once reached, this result
                is returned to the caller.
            
            Examples:
                >>> self.evaluate_expression("15+(9*2)")
                "33"
                >>> self.evaluate_expression("15+(9*2)+(8-4)")
                "37"
                >>> self.evaluate_expression("15+(9*2+(8-4))+5")
                "42"
            """
        
        print(expr)
        # No more opening brackets, evaluate the remaining as standard expression
        if not any(bracket in expr for bracket in "([{"):
            return self.calculate(expr, False)
        
        # Find the innermost closing bracket 
        # We look for the first closing bracket and find its corresponding opening one.
        target_close = -1
        for i, char in enumerate(expr):
            if char in ")]}":
                target_close = i
                break
                
        target_open = -1
        for i in range(target_close, -1, -1):
            if expr[i] in "([{":
                target_open = i
                break
                
        # Extract inner content 
        inner_expr = expr[target_open + 1:target_close]
        
        #  Calculate the inner expression
        inner_result = self.calculate(inner_expr, True)

        
        # Replace the bracketed part with the evaluated result
        new_expr_with_simplified_answer_replacement = expr[:target_open] + str(inner_result) + expr[target_close+1:]

        # Recursively call with the updated string
        return self.evaluate_expression(new_expr_with_simplified_answer_replacement)

    def clean_expression(self, expression_to_clean: str) -> str:
        """removes all white space from the expression in case a space or tab was entered.
        
        Args:
            expression_to_clean (string): entered expression
        
        Returns:
            string: altered expression with no white space. 
        
        Examples:
            >>> self.clean_expression("15+(9 *2)")
            "15+(9*2)"
            >>> self.clean_expression("15+(9* 2)+(8- 4)")
            "15+(9*2)+(8-4)"
        """
        elements = expression_to_clean.split()
        expression_to_clean = "".join(elements)

        return expression_to_clean

    def get_num_operators(self,expression: str) -> int:
        """gets the number of operations that are to be done in the expression. If the expression is from the inside of parenthesis it gets only 
            the number of operations in side the parenthesis
        
        Args:
            expression (string): number of operators found in the expression
        
        Returns:
            int: number of operators found in the expression
        
        Examples:
            >>> self.get_num_operators("15+9*2")
            2
            >>> self.get_num_operators("15+9*2+8-4")
            4
        """
        num_operators = 0
        for i, char in enumerate(expression):
            if char in self._OPERATORS:
                if not (char=="-" and i == 0) and not (char == "-" and ((expression[i - 1] in self._OPERATORS))): # skip negative numbers - don't count them as 
                    num_operators += 1

        return num_operators

    def find_operator_pos(self,expr: str, precidence: str = 'mult_div') -> int:
        """finds the next operator in the expression that should be solved next, assuming multiplication and division first
        
        Args:
            expr (string): number of operators found in the expression
            precidence (string): precidence to look for

        Returns:
            int: position of operator to solve for next
        
        Examples:
            >>> self.find_operator_pos("15+9*2", "add_sub")
            4
            >>> self.find_operator_pos("15*9+2+8-4")
            2
        """
        if precidence == "mult_div": 
            operators = ["*", "/", "%"]
        elif precidence == "exponent":
            operators = ["^"]
            if "^" in expr:
                first_operator = expr.rfind("^")
                return first_operator
        else:
            operators = ["+", "-"]

        first_operator = -1
        for i, char in enumerate(expr):
            if char in operators:
                if not (char=="-" and i == 0):
                    first_operator = char 
                    break # Stop at the first match
        
        if first_operator == -1:
            return -1
        if first_operator == "-" and expr[0] == "-":
            return expr.find(first_operator, 1)
        
        return expr.find(first_operator)

    # Gets the single operator expression we will be solving for from the overal expression
    def get_subexpression(self,expression: str, pos_operator: int) -> tuple[str, int, int]:
        """gets the sub expression to solve for from the entered expression
        
        Args:
            expression (string): number of operators found in the expression
            pos_operator (int): position of operator that should be solved for

        Returns:
            tuple: string, int, int: sub expression to solve for, left most position of the sub expression in the overall expression,
                right most position of the sub expression in the overall expression.
        
        Examples:
            >>> self.get_subexpression("15+9*2", 4)
            "9*2", 3, 6
            >>> self.get_subexpression("15*9+2+8-4", 2)
            "15*9", 0, 4 
        """
        # Find the left most postion for the sub expression in the overall expression
        left = pos_operator - 1    
        while  (left >= 0 and expression[left] not in self._OPERATORS):
            left -= 1
        left += 1

        if left == 1 and expression[0] == "-": left = 0 # include leading negative sign if needed
        
        # Find the right most postion for the sub expression in the overall expression
        right = pos_operator + 1

        if expression[right] == "-": # check for negative numbers
            right += 1 # move right one more to include the negative sign
    
        while right < len(expression) and expression[right] not in self._OPERATORS: 
            right += 1

            
        
        sub_exp = expression[left:right]
        
        return sub_exp, left, right

    add = lambda self, num_1 = 0, num_2 = 0: num_1 + num_2
    sub = lambda self,num_1 = 0, num_2 = 0: num_1 - num_2
    float_div = lambda self, num_1 = 1, num_2 = 1: num_1 / num_2
    mult = lambda self, num_1 = 1, num_2 = 1: num_1 * num_2

    def do_the_math(self, first_num: float, second_num: float, operator: str) -> float:
        """performs the actual math on the single operator expressions that are passed to it using the lambda expressions 
            above the function definition
        
        Args:
            first_num (float): first number of the expression
            second_num (float): second number of the expression
            operator (string): the operator character from the expression

        Returns:
            float: answer to the expression that was passed
        
        Examples:
            >>> self.do_the_math("9*2")
            18.0
            >>> self.do_the_math("15+18.0")
            33.0 
        """

        # these are all lambda calls which can be found just above the function definition for self.do_the_math
        match operator:
            case "+":
                return float(self.add(first_num, second_num))
            case "-":
                return float(self.sub(first_num, second_num))
            case "*":
                return float(self.mult(first_num, second_num))
            case "/":
                if second_num == 0:
                    raise CalculatorError(f"Division by zero encountered while calculating: {first_num} / {second_num}. Setting answer to 0.0")
                    
                return self.float_div(first_num, second_num)
            case "%":
                if second_num == 0:
                    raise CalculatorError(f"Modulo by zero encountered while calculating: {first_num} % {second_num}. Setting answer to 0.0")

                return float(first_num % second_num)
            case "^":
                return self.get_exponent_answer(first_num, second_num)

        raise CalculatorError(f"Unknown operator '{operator}")

    def get_exponent_answer(self, base: float, exponent: float) -> float:
        """calculates the exponent of a base number raised to the power of exponent
        
        Args:
            base (float): base number
            exponent (float): exponent number

        Returns:
            float: answer to the expression that was passed
        
        Examples:
            >>> self.get_exponent_answer(2,3)
            8.0
            >>> self.get_exponent_answer(9,0.5)
            3.0 
        """
        if base == 0 and exponent == 0:
            print("Warning: 0^0 is undefined. Treating as 1.")
            return 1.0

        # Reject negative base + non-integer exponent - creates complex numbers, calculator designed for real numbers only
        if base < 0 and not exponent.is_integer():
            raise CalculatorError("Error: Negative base with non-integer exponent results in complex number (not supported).")

        try:
            answer = base ** exponent
            # make sure we didn't create a complex number
            if isinstance(answer, complex):
                raise CalculatorError("Error: Calculation produced a complex number.")
        except OverflowError: # everything has a limit
            raise CalculatorError("Error: Result too large to represent.")
        except Exception as e: # unknown, print it and restart
            raise CalculatorError(f"Error during exponentiation: {str(e)}")

        # long floats are silly, we aren't trying to find the black hole way over there -----------------------------------------------> 
        formatted = f"{answer:.9f}"
        return float(formatted)

    def which_operator(self, expression_to_calc: str) -> int:
        """controls the precidence for which operator self.find_operator_pos should be looking for
        
        Args:
            expression_to_calc (string): entered expression

        Returns:
            int: position of the next operator that should be solved for
        
        Examples:
            >>> self.which_operator("9+2")
            1
            >>> self.which_operator("15+18*4")
            5
        """

        pos_operator = self.find_operator_pos(expression_to_calc, "exponent")
        if pos_operator == - 1: pos_operator = self.find_operator_pos(expression_to_calc) # no precidence flag so it assumes multiplicatoin and division
        if pos_operator == - 1: pos_operator = self.find_operator_pos(expression_to_calc, "add_sub")


        return pos_operator

    def get_elements(self, expr: str, left: int, right: int, op: int) -> tuple[float, float, str]:
        """gets the elements of the expression we are currently solving for
        
        Args:
            expr (string): entered expression
            left (int): position of the left most digit(s)
            right (int): position of the right most digit(s)
            op (int): position of the operator for the expression

        Returns:
            tuple float, float, str: returns the first number, second number and the operator character
        
        Examples:
            >>> self.get_elements("9+2", 0, 3, 1)
            9.0, 2.0, "+"
            >>> self.get_elements("15+18*4", 3, 7, 5)
            18.0, 4.0, "*"
        """

        first = float(expr[left:op])
        second = float(expr[op + 1: right])
        operator = expr[op: op + 1]

        return first, second, operator

    def calculate(self, expr: str, is_paren_exp: bool) -> str:
        """Calculates the expression passed to it. It is either the entered expression or the expression in parenthesis, main function for handling 
            calculations from sub-expresions
        
        Args:
            expr (string): entered expression or parenthesis expression
            is_paren_exp (bool): flags if this is an expression from a parenthesis or not (controls step by step output)

        Returns:
            string: returns modified expr replacing any sub-expressions that were solved with their answers
        
        Examples:
            >>> self.calculate("9*5",True)
            "40"
            >>> self.calculate("15+18*4", False)
            "87"
            >>> self.calculate("15.6+18*4", False)
            "87.6"
        """
        # if paren drop we could wind up with a double neg next to a valid operator. 
        # We need to fix this here or we get a float error

        douuble_neg_pos = expr.find("--")
        if douuble_neg_pos != -1:
            if douuble_neg_pos == 0: 
                expr = expr.replace("--", "")
            else:
                expr = expr.replace("--", "+")
                expr = self.strip_odd_double_operators(expr)

        # how many operators are in the expression
        num_operators = self.get_num_operators(expr)

        # loop for each operator in the expression
        for i in range(num_operators):
            pos_operator = self.which_operator(expr) # get the operator position to solve for next based on precidence PEMDAS

            # get the math problem we are going to solve along with that problems first and last position in the over all expression
            sub_exp, left_num, right_num = self.get_subexpression(expr, pos_operator)
            
            first_num, second_num, operator = self.get_elements(expr, left_num, right_num, pos_operator) # Gets the elements of the expression to solve for

            try:
                answer = self.do_the_math(first_num, second_num, operator)
            except CalculatorError as e:
                print(f"Error: {str(e)}")
                return "ERROR"
            
            if answer.is_integer(): 
                answer = int(answer) # convert to int if no decimal portion
                
            expr = expr.replace(sub_exp, str(answer)) # replace the math problem we just answered with the actual answer in the original expression
            if is_paren_exp == False: 
                print(expr)

        return expr

    def strip_odd_double_operators(self, expr) -> str:
        for i, each in enumerate(expr):
            if each == "+":
                prev_each = expr[i - 1]
                if prev_each in self._OPERATORS:
                    expr = expr[:i] + expr[i + 1:]

        return expr

    def get_do_another(self) -> str:
        """Prompts the user, asking if they would like to enter another expression. Defaults to yes. 
        
        Args:
            NONE

        Returns:
            string: returns 'y', 'n' or '' ('' is the default to 'y')
        
        Examples:
            >>> self.get_do_another()
            'y'
            >>> self.get_do_another()
            "n"
        """
        prompt = "do another calculation? [Y/n] "
        error_prompt = "ERROR: invalid input. Please enter 'y' or 'n' "

        while True:
            another = str(input(prompt)).strip().lower()
            if another != "n" and another != "y" and another != "":
                print(error_prompt)
            else:
                return another

    def is_balanced_paren(self, expr: str) -> tuple[bool, str]:
        """verifies that the parenthesis are balanced and fixes single digit parenthesis like 4*(5) to 4*5 
            or (5)*4 to 5*4
        
        Args:
            expr (string): the string that we are validating

        Returns:
            tuple bool, bool, string: returns a tuple with the first value being if the parenthesis are balanced and 
                the second value being if there is an ambiguous parenthesis and the third value being the potentially modified expression
                from fix_double_neg_at_beg_of_expr.
        
        Examples:
            >>> is_balanced_paren("4*(5+2)")
            True, "4*(5+2)"       
            >>> is_balanced_paren("4*(5+2)")
            True, "4*(5+2)"
            >>> is_balanced_paren("4*(5+2]")
            False, "4*(5+2]"
            >>> is_balanced_paren("4*[5+2]")
            False, "4*[5+2])"
        """

        return self.return_bal_paren_or_ambiguous(expr, True)

    def return_bal_paren_or_ambiguous(self, expr: str, check_paren: bool) -> tuple[bool, str]:
        """helper function for is_balanced_paren and is_ambiguous 
            that returns if the parenthesis are balanced or if the expression could be ambiguous
            depending on how the check_paren flag is set
        
        Args:
            expr (string): the string that we are validating
            check_paren (bool): flag to check for balanced parenthesis or ambiguous parenthesis

        Returns:
            tuple bool, string: returns a tuple with the first value being if the parenthesis are balanced or 
                if there is an ambiguous parenthesis based on the chck_paren flag and the second value being 
                the expression passed in.
        
        Examples:
            >>> return_bal_paren_and_ambiguous("4*(5+2)", True)
            True, "4*(5+2)"
            >>> return_bal_paren_and_ambiguous("4(5+2)", False)
            True, "4(5+2)"
        """
        result = False
        stack = []
        pairs = {')': '(', ']': '[', '}': '{'}
        
        for i, char in enumerate(expr):
            if char in pairs.values():          # opening: (, [, {
                stack.append(char)

                # Check for Ambiguous expressions like 4(5+2) or (5+2)4
                if i - 1 >= 0 and check_paren == False:                     
                    if expr[i - 1].isdigit():
                        result = True
                        return result, expr
                    
                # fix singledigit parenthesis like 4*(5), (5)*4, -(5)*4 and -(-5)*4 and check for balanced paren again
                expr, has_changed_expr = self.fix_double_neg_at_beg_of_expr(expr, i)
                if has_changed_expr:
                    stack.pop()
                    result, expr = self.return_bal_paren_or_ambiguous(expr, True)
                    break
                
            elif char in pairs: 
                if i + 1 <= len(expr) - 1:                # closing: ), ], }
                    if  expr[i + 1].isdigit() and check_paren == False:
                        result = True
                        return result, expr
                
                if not stack or stack.pop() != pairs[char]:
                    result = False
                    return result, expr
                
        if len(stack) == 0 and check_paren == True: result = True
        return result, expr

    def is_ambiguous(self, expr: str) -> bool:
        """Checks to see if the expression is ambiguous. An expression is ambiguous if there are parenthesis that do not have an operator to the left or right of them. 
            For example, 4(5+2) is ambiguous because it could be 4*(5+2) or 45+2. (5+2)4 is also ambiguous because it could be (5+2)*4 or 5+24.
        
        Args:
            expr (string): the string that we are validating 

        Returns:
            bool: returns true if the expression is ambiguous, false otherwise.
        
        Examples:
            >>> is_ambiguous("4*(5+2)")
            False
            >>> is_ambiguous("4(5+2)")
            True
            >>> is_ambiguous("(5+2)4")
            True
        """
        result, expr = self.return_bal_paren_or_ambiguous(expr, False)
        return result

    def fix_double_neg_at_beg_of_expr(self, expr: str, open_paren_pos: int) -> tuple[str, bool]:
        """checks the beginning of the expression for a negitive just outside the open parenthesis and a 
            negative just inside the parenthesis. If this is the case, it fixes the expression by 
            removing both negative signs. This simplifies the expressioin from a double negative to a
            positive and also allows us to avoid issues with double negatives when we drop parenthesis. 
            This is the only case of single digit parenthesis that we need to worry about because any 
            other case of single digit parenthesis would be caught by other checks that are done. 

        Args:
            expr (string): the string that we are
            open_paren_pos (int): position of the opening parenthesis

        Returns:
            tuple string, bool: returns the modified expression and a flag indicating if a change was made

        Examples:
            >>> fix_double_neg_at_beg_of_expr("4*(5+2)", 1)
            "4*(5+2)", True
            >>> fix_double_neg_at_beg_of_expr("12*(5+2)", 2)
            "12*(5+2)", False
        """
        has_changed_expr = False

        if expr[0] == "-" and expr[1] == "(" and expr[2] == "-": # check for negative sign outside and inside the parenthesis
            expr = "(" + expr[3:]
            has_changed_expr = True 
        
        return expr, has_changed_expr

    def is_valid_input(self, input_to_validate: str) -> bool:
        """Checks to make sure that input is only 0-9 . ()+-*/[]{}^%
            also checks for matching parenthesis
            also checks to make sure that if there are parenthesis, 
                that expression to the right and left of them start with an operator and not a number 
            also checks for division by 0
            also checks for double operators
            also checks for trailing or leading operators
        
        Args:
            input_to_validate (string): the input the user provided

        Returns:
            bool: True if valid and False if an error was found
        
        Examples:
            >>> is_valid_input("5*7+(4/2)")
            "valid"
            >>> is_valid_input("5*7a+(4/2)")
            "invalid input, please only use 0-9 . + - * / ( )[]{}^% characters only for the expression."
        """
        valid = "1234567890.()+-*/[]{}^%"
        div_by_0 = ["/0", "%0"]
        val = True

        # make sure someone didn't just hit enter
        if not input_to_validate:
            print("invalid input, expression can not be blank.")
            val = False

        # check for valid characters
        if not all(char in valid for char in input_to_validate):
            print("invalid input, please only use 0-9 . + - * / ( )[]{}^% characters only for the expression.")
            val = False

        # Check for leading or trailing operators
        if val and self.has_leading_or_trailing_op(input_to_validate):
            print("Expression has leading or trailing operator(s) ")
            val = False

        # Check for balanced parenthesis and ambiguous parenthesis - also fixs single digit paren
        if val and any(char in input_to_validate for char in "[]{}()"):
            val, input_to_validate = self.is_balanced_paren(input_to_validate)
            if val == False: print("Parenthesis mis-match")
        
        if val and any(char in input_to_validate for char in "[]{}()"):
            result = self.is_ambiguous(input_to_validate)
            if result == True: 
                print("Ambiguous parenthesis detected - operator required before and/or after parenthesis to avoid ambiguity") 
                val = False
        
        # Check for double operators
        if val and self.has_double_op(input_to_validate):
            print("Double operator detected")
            val = False
        
        # Check for division by 0
        if val and any(char in input_to_validate for char in div_by_0):
            print("Division by 0 error, can not divide or MOD by 0")
            val = False

        # Check for valid numbers (only one decimal per number)
        if val and not self.is_valid_numbers(input_to_validate):
            print("Invalid number - more than one decimal")
            val = False
            
        if val:
            if any(char in input_to_validate for char in ["()","[]", "{}"]):
                print("Empty brackets detected, they will be removed from the expression")

        return val, input_to_validate

    def is_valid_numbers(self, expr: str) -> bool:
        """Ensures there is only one decimal in each number in the expression
        
        Args:
            expr (string): the string that we are checking

        Returns:
            bool: returns true if all numbers are valid for calculation, false otherwise.
        
        Examples:
            >>> is_valid_numbers("-5*7+(4/2)")
            True
            >>> is_valid_numbers("5.1*7+(4/2)")
            True
            >>> is_valid_numbers("5*7.992+-(4/2)")
            True
            >>> is_valid_numbers("*5*7+(4.2.3/2)")
            False
        """
        cur_num = ""
        
        for char in expr:
            if char.isdigit() or char == '.':
                cur_num += char
            else:
                if cur_num.count('.') > 1:
                    return False
                cur_num = ""
        
        # check the last number
        if cur_num.count('.') > 1:
            return False

        return True

    def has_double_op(self, expr: str) -> bool:
        """Checks the expression to see if there are double operators. 
            Will ignore an expression that double negative signs, or negative signs after the operator.
        
        Args:
            expr (string): the string that we are checking

        Returns:
            bool: returns true if there is a double operators, false otherwise.
        
        Examples:
            >>> has_double_op("-5*7+(4/2)")
            False
            >>> has_double_op("*5*7++(4/2)")
            True
            >>> has_double_op("5*7+-(4/2)")
            False
            >>> has_double_op("*5*7+(4//2)")
            True
        """
        for i in range(len(expr) - 1):

            if expr[i] in self._OPERATORS:

                if expr[i + 1] in self._OPERATORS and not expr[i + 1] == "-":
                    return True
        return False


    def has_leading_or_trailing_op(self, expr: str) -> bool:
        """Checks the expression to see if there are leading or trailing operators. 
            Will ignore an expression that starts with a negative sign.
        
        Args:
            expr (string): the string that we are checking

        Returns:
            bool: returns true if there is a leading or trailing operator, false otherwise.
        
        Examples:
            >>> has_leading_or_trailing_op("-5*7+(4/2)")
            False
            >>> has_leading_or_trailing_op("*5*7+(4/2)")
            True
            >>> has_leading_or_trailing_op("5*7+(4/2)-")
            True
            >>> has_leading_or_trailing_op("*5*7+(4/2)*")
            True
        """
        expr_len = len(expr)
        char = expr[expr_len - 1]
        
        if char in self._OPERATORS:
            return True
        
        char = expr[0]
        if char in self._OPERATORS:
            if char != '-':
                return True

        return False

    def get_num_input(self) -> str:
        """Collects the input from the user, cleans it and calls the validation sequence on it passing any validation issues onto the user
        
        Args:
            NONE

        Returns:
            string: a valid expression
        
        Examples:
            >>> get_num_input("5*7+(4/2)")
            "5*7+(4/2)"
            >>> get_num_input("5*7a+(4/2)")
            outputs error message and asks for input again
        """
        greeting = "Please enter your expression (use '%' for MOD and '^' for exponents): "
        val = False

        while True:
            try:
                expr = input(greeting)
                expr = self.clean_expression(expr)
                expr = self.normalize_unary(expr)
                val, expr = self.is_valid_input(expr)

                if val:
                    return expr
            except ValueError as exception:
                print(str(exception))

    def normalize_unary(self, expr: str) -> str:
        """Replace patterns like -- → +, +- → -, -+ → -, ++ → + and remove leading +"""
        while any(char in expr for char in ["*-(-", "/-(-", "+-(-", "--(-"]):
            expr = (expr.replace("*-(-", "*(")
                        .replace("/-(-", "/(")
                        .replace("+-(-", "+(")
                        .replace("--(-", "-(")
                        .replace("^--(", "^+("))
        
        # Replace double signs first (order matters a bit)
        while any(char in expr for char in ["--", "+-", "-+", "++"]):
            expr = (expr.replace("--", "+")
                        .replace("+-", "-")
                        .replace("-+", "-")
                        .replace("++", "+")
                        .replace("^^", "^"))
        
        # Collapse multiple (e.g. --- → -)
        while any(char in expr for char in ["---", "----"]):
            expr = expr.replace("---", "-").replace("----", "+")  # crude but covers common cases
        
        # Remove leading +
        if expr.startswith("+"):
            expr = expr[1:]
        
        return expr

    def main(self) -> None:
        """main entry for the program calls get_num_input once that is return with valid input it calls pars_expression to do the rest of the work
            then it asks if the user wants to do another expression.
        
        Args:
            NONE

        Returns:
            NONE
        
        Examples:
            >>> main()
        """
        do_another = True
        while do_another:
            expr = self.get_num_input()
            
            result = self.evaluate_expression(expr)
            if result == "ERROR":
                print("Calculation could not be completed due to previous error(s).")
            else:
                print(f"Final answer: {result}")

            do_another_ans = self.get_do_another()

            if do_another_ans == "n":
                do_another = False
                
    def __init__(self):
        self._OPERATORS = set(["*","/", "+", "-", "^", "%"])

calc = HoldenRowlandCalculator()
calc.main()