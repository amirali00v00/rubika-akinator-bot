import akinator

print("================================")
print("AKINATOR RENDER TEST")
print("================================")

try:
    print("1. Creating Akinator object...")

    aki = akinator.Akinator()

    print("2. Object created successfully.")

    print("3. Starting game...")

    aki.start_game()

    print("4. SUCCESS!")
    print("Question:")
    print(aki.question)

except Exception as e:

    print("5. FAILED!")
    print("Error type:", type(e).__name__)
    print("Error:", repr(e))
