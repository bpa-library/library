
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# def backblaze():
def backblaze_store():
    try:
        b = boto3.client(
            's3',
            endpoint_url=os.getenv('B2_ENDPOINT'),
            aws_access_key_id=os.getenv('B2_KEY_ID'),
            aws_secret_access_key=os.getenv('B2_APP_KEY'),
            region_name=os.getenv('region_name')
        )
        print(f"**Backblaze B2 innitiate: {'✅ Connected' if b else '❌ Disconnected'}")
        return b
        # return boto3.client(
        #     's3',
        #     endpoint_url=os.getenv('B2_ENDPOINT'),
        #     aws_access_key_id=os.getenv('B2_KEY_ID'),
        #     aws_secret_access_key=os.getenv('B2_APP_KEY'),
        #     region_name=os.getenv('region_name')
        # )
    except Exception as e:
        print(f"❌ Backblaze B2 connection failed: {str(e)}")
        return False


def check_backblaze_status():
    try:
        print(f"**Backblaze B2: {'✅ Connected' if backblaze_store() else '❌ Disconnected'}")
    except Exception as e:
        print(f"❌ Backblaze B2 check failed: {e}")
        return False
    
# def check_file_exists(bucket_name, file_path):
#     """Check if a file exists in Backblaze B2"""
#     try:
#         s3 = backblaze_store()
#         s3.head_object(Bucket=bucket_name, Key=file_path)
#         return True
#     except Exception as e:
#         print(f"File does not exist or inaccessible: {file_path}")
#         print(f"Error: {str(e)}")
#         return False

# # Test with your file path
# file_exists = check_file_exists(
#     'Audio-Library-SRN', 
#     'Bharat na 75 filmudhyog na shreshth kasabio By Nirali badiyani/aud001.mp3'
# )

