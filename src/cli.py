from aedificator.main import Main

if __name__ == "__main__":
    try:
        AedificatorClient = Main()
    except Exception as err:
        print(f"Error during execution: {err}")
