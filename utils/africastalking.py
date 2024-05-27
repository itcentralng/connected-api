import os
from dotenv import load_dotenv
import africastalking
from fastapi import HTTPException

load_dotenv()

africastalking.initialize(
    username=os.environ.get("AFRICASTALKING_USERNAME"),
    api_key=os.environ.get("AFRICASTALKING_API_KEY"),
)


class AfricasTalking:
    sms = africastalking.SMS

    def send(self, sender, message, recipients):
        try:
            response = self.sms.send(message, recipients, sender)
            print(f"message sent to {recipients}")
        except Exception as e:
            print(f"Houston, we have a problem: {e}")
            raise HTTPException(status_code=500, detail="Failed to send message")
