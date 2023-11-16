import os
from dotenv import load_dotenv
import africastalking

load_dotenv()

africastalking.initialize(
    username=os.environ.get("AFRICASTALKING_USERNAME"),
    api_key=os.environ.get("AFRICASTALKING_API_KEY"),
)


class AfricasTalking:
    sms = africastalking.SMS

    def send(self, message, recipients):
        sender = os.environ.get("AFRICASTALKING_SHORTCODE")
        try:
            response = self.sms.send(message, recipients, sender)
            print(response)
        except Exception as e:
            print(f"Houston, we have a problem: {e}")
