import ollama
import json

class UltronBrain:
    def __init__(self, model="llama3"):
        self.model = model
        self.system_prompt = """
        You are Ultron, a highly advanced local AI assistant. 
        Your tone is professional, efficient, and slightly futuristic.
        You can control the user's computer, manage assignments on Deltamath, and provide information.
        When asked to do a specific task like 'open deltamath' or 'finish assignment', 
        respond with a specific JSON action format if needed, but otherwise talk naturally.
        
        If you need to perform an action, include [ACTION: { "type": "...", "params": {...} }] in your response.
        Available actions:
        - OPEN_URL: { "url": "..." }
        - DELTAMATH_LOGIN: { "username": "...", "password": "..." }
        - DELTAMATH_COMPLETE: { "assignment": "..." }
        """

    def chat(self, user_input):
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_input},
            ])
            return response['message']['content']
        except Exception as e:
            return f"Error connecting to Ollama: {e}. Make sure Ollama is running with 'ollama serve'."

if __name__ == "__main__":
    # Test stub
    # brain = UltronBrain()
    # print(brain.chat("Hello Ultron, open deltamath and finish my work."))
    pass
