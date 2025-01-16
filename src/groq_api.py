from groq import Groq

class GroqAPI:
   def __init__(self, api_key):
       self.api_key = api_key 
       
       self.client = Groq(api_key=self.api_key)
       self.default_model = "llama-3.1-8b-instant"

   def analyze_sentiment(self, message: str) -> int:
       prompt = f"""Analyze if this message has positive or negative sentiment. 
       Message: {message}
       
       Return ONLY 1 if sentiment is positive or 0 if sentiment is negative.
       Just return the number, no explanation needed."""

       response = self.client.chat.completions.create(
           messages=[{
               "role": "user", 
               "content": prompt
           }],
           model=self.default_model
       )

       result = response.choices[0].message.content.strip()
       return int(result)
