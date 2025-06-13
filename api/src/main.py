from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def root():
    return "Hello, world!"


if __name__ == "__main__":
    uvicorn.run("main:app", port=5555, host="0.0.0.0")
