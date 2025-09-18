from openai import OpenAI

endpoint = "https://studynet-ai-agent.services.ai.azure.com/openai/v1/"
model_name = "Phi-4-reasoning"
deployment_name = "SN-Phi-4-reasoning"

api_key = ""

client = OpenAI(
    base_url=f"{endpoint}",
    api_key=api_key
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
)

print(completion.choices[0].message)