from fastapi import FastAPI
import service

app = FastAPI(title="NLP Simple API")

@app.get("/ask")
def ask_question(pergunta: str, debug: bool = False):
    """
    Endpoint principal para realizar perguntas utilizando RAG.
    """
    return service.completion(pergunta, debug)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
