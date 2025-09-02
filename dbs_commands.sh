docker run --name postgres --rm -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=development -e PGDATA=/var/lib/postgresql/data/pgdata -v /tmp:/var/lib/postgresql/data -p 5432:5432 -d or -it postgres
docker run --name redis -p 6379:6379 -it redis:latest
docker run --name redis -p 6379:6379 -p 8001:8001 redis/redis-stack # redis with GUI on 8001
docker run \
   -p 9000:9000 \
   -p 9001:9001 \
   --name minio \
   -v ~/minio/data:/data \
   -e "MINIO_ROOT_USER=admin" \
   -e "MINIO_ROOT_PASSWORD=password" \
   quay.io/minio/minio server /data --console-address ":9001"
# s3 with GUI on 9001

celery -A api.src.celery_app flower
celery -A api.src.celery_app worker