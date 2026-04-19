from legal_engine import run_pipeline

if __name__ == "__main__":
    while True:
        query = input("\nEnter crime scenario: ")
        result = run_pipeline(query)

        print("\n⚖️ Legal Output:\n")
        print(result)