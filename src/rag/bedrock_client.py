
import boto3
from botocore.exceptions import ClientError


AWS_PROFILE = "financial-ai"
AWS_REGION = "eu-north-1"

MODEL_ID = "eu.amazon.nova-micro-v1:0"


class BedrockClient:
    def __init__(self):
        session = boto3.Session(
            profile_name=AWS_PROFILE,
            region_name=AWS_REGION
        )

        self.client = session.client(
            "bedrock-runtime"
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 300
    ) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self.client.converse(
                modelId=MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": 0.0
                }
            )

            content = response["output"]["message"]["content"]

            return "\n".join(
                block["text"]
                for block in content
                if "text" in block
            )

        except ClientError as error:
            code = error.response["Error"]["Code"]
            message = error.response["Error"]["Message"]

            raise RuntimeError(
                f"Bedrock error [{code}]: {message}"
            ) from error


def main():
    bedrock = BedrockClient()

    prompt = (
        "Answer in one short sentence: "
        "What is the purpose of financial "
        "statement analysis?"
    )

    print("Calling Amazon Bedrock...")

    answer = bedrock.generate(
        prompt,
        max_tokens=100
    )

    print("\n=== BEDROCK RESPONSE ===")
    print(answer)


if __name__ == "__main__":
    main()
