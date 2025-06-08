def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    return x / y

print("Select operation:")
print("1. Add")
print("2. Subtract")
print("3. Multiply")
print("4. Divide")

operation = input("Enter the number of the operation you want to perform: ")

num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))

if operation == '1':
    print(num1, "+", num2, "=", add(num1, num2))
elif operation == '2':
    print(num1, "-", num2, "=", subtract(num1, num2))
elif operation == '3':
    print(num1, "*", num2, "=", multiply(num1, num2))
elif operation == '4':
    if num2 != 0:
        print(num1, "/", num2, "=", divide(num1, num2))
    else:
        print("Cannot divide by zero.")
else:
    print("Invalid input")