from aedificator.main import Main
import traceback

if __name__ == "__main__":
    try:
        AedificatorClient = Main()
    except Exception as err:
        print(f"Error during execution: {traceback.format_exc()}")
