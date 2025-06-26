import aioboto3
from botocore.exceptions import ClientError
from types_aiobotocore_s3 import Client

from tempfile import SpooledTemporaryFile


class S3Client:
    def __init__(self,
                 endpoint_url: str,
                 access_key: str,
                 secret_key: str,
                 bucket_name: str,
                 ):
        self._config = {
            "service_name": "s3",
            "endpoint_url": endpoint_url,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": 'us-east-1',
        }

        self.bucket_name = bucket_name
        self._session = aioboto3.Session()
        self._client: Client = None

    async def __aenter__(self):
        self._client = await self._session.client(**self._config).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def get(self, file_name: str) -> bytes | None:
        try:
            response = await self._client.get_object(Bucket=self.bucket_name, Key=file_name)
            print(response)
            content = await response['Body'].read()
            # content.decode()
            return content
        except ClientError as err:
            print(err)
            return None

    async def get_link(self, file_name: str, expires_in: int = 3600) -> str | None:
        try:
            await self._client.get_object(Bucket=self.bucket_name, Key=file_name)

            return await self._client.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_name},
                ExpiresIn=expires_in,
            )
        except ClientError as err:
            print(err)
            return None

    async def upload(self, file_obj: SpooledTemporaryFile, file_name: str) -> None:
        try:
            await self._client.upload_fileobj(Fileobj=file_obj, Bucket=self.bucket_name, Key=file_name)
        except ClientError as err:
            print(err)

    def delete(self):
        ...

    def delete_bulk(self):
        ...

# # Создание bucket
# await s3.create_bucket(Bucket=BUCKET)
# print(f'Bucket "{BUCKET}" создан')


# # Список файлов в bucket
# listed = await s3.list_objects_v2(Bucket=BUCKET)
# print('Объекты в bucket:', [obj['Key'] for obj in listed.get('Contents', [])])
#