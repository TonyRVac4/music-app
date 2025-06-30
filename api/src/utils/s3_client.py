from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError
from io import BytesIO


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
        self._session = aioboto3.Session()
        self.bucket_name = bucket_name

    @asynccontextmanager
    async def _get_client(self):
        async with self._session.client(**self._config) as client:
            yield client

    async def check(self, file_name: str) -> bool:
        async with self._get_client() as client:
            try:
                await client.head_object(Bucket=self.bucket_name, Key=file_name)
                return True
            except ClientError:
                return False

    async def get_link(self, file_name: str, expires_in: int = 600) -> str | None:
        async with self._get_client() as client:
            try:
                return await client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_name},
                    ExpiresIn=expires_in,
                )
            except ClientError as err:
                return None

    async def upload(self, file_obj: BytesIO, filename: str) -> None:
        async with self._get_client() as client:
            try:
                await client.upload_fileobj(
                    Fileobj=file_obj, Bucket=self.bucket_name, Key=filename,
                )
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
