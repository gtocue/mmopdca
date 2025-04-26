from fastapi import FastAPI

app = FastAPI(title="mmopdca – proof-of-life")

@app.get("/")
def root():
    return {"msg": "mmopdca is alive 🚀"}
