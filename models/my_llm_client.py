from groq import Groq

class LLMClient:

    def __init__(self):
        self.client = Groq(api_key="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")

    def generate(self, prompt):

        print("⚡ Calling Groq LLM...")
        print("📨 Prompt Sent:", prompt[:200], "...")

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            print("✅ Groq Response Received")
            print("📦 Full Response Object:", response)

            content = response.choices[0].message.content.strip()

            print("📄 LLM Output:", repr(content))
            return content

        except Exception as e:
            print("❌ Groq Failed:", e)
            return ""
