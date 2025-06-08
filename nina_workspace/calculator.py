# Define the functions for each operation
def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y

# Get user input for the operation and numbers
operation = input("Enter an operator (+, -, *, /): ")
num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))

# Perform the selected operation and display the result
if operation == "+":
    print(add(num1, num2))
elif operation == "-":
    print(subtract(num1, num2))
elif operation == "*":
    print(multiply(num1, num2))
elif operation == "/":
    print(divide(num1, num2))
else:
    print("Invalid operator. Please use one of the following: +, -, *, /")
