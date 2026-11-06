from fastapi import FastAPI
from routers import auth, production, equipment, complaints, instructions

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(production.router)
app.include_router(equipment.router)
app.include_router(complaints.router)
app.include_router(instructions.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0", port=8000)