def bool_prompt(msg: str) -> bool:
    while True:
        response = input(f"{msg} [y/n]: ").lower()

        if response == "y":
            return True
        elif response == "n":
            return False
        else:
            print(f"'{response}' is an invalid option.")
