
import boto3
from botocore.exceptions import BotoCoreError, ClientError

PROFILE = "financial-ai"
REGION = "eu-north-1"
BUCKET = "financial-document-intelligence-bucket"


def main():
    try:
        session = boto3.Session(
            profile_name=PROFILE,
            region_name=REGION
        )

        s3 = session.client("s3")

        response = s3.list_objects_v2(
            Bucket=BUCKET,
            Delimiter="/"
        )

        print("Connexion AWS S3 réussie !")
        print(f"Bucket : {BUCKET}")
        print(f"Région : {REGION}")

        print("\nDossiers disponibles :")
        for prefix in response.get("CommonPrefixes", []):
            print(f" - {prefix['Prefix']}")

    except (BotoCoreError, ClientError) as error:
        print(f"Erreur AWS : {error}")
        raise


if __name__ == "__main__":
    main()
