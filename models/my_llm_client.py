from huggingface_hub import InferenceClient


class LLMClient:
    def __init__(self):
        self.client = InferenceClient(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            token="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"
        )

    def generate(self, prompt: str) -> str:
        print("⚡ Calling Hugging Face LLM...")
        print("📨 Prompt Sent:", prompt[:200], "...")

        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1024
            )

            content = response.choices[0].message.content.strip()

            print("✅ Hugging Face Response Received")
            print("📄 LLM Output:", repr(content))
            return content

        except Exception as e:
            print("❌ Hugging Face Failed:", e)
            return ""
