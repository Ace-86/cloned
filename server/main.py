# uvicorn main:app
# uvicorn main:app --reload

#main imports
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
import openai

# custom function imports
from functions.openai_requests import convert_audio_to_text, get_chat_response
from functions.database import store_messages, reset_messages
from functions.text_to_speech import convert_text_to_speech

# Intiate App
app = FastAPI()


# CORS - Origins
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://localhost:4174",
    "http://localhost:3000",
]

# CORS - Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials= True, 
    allow_methods= ["*"], 
    allow_headers= ["*"], 
)

# Health Report
@app.get("/health")
async def check_health():
    return {"message": "Healthy"}

# Reset messages
@app.get("/reset")
async def reset_convo():
    reset_messages()
    return {"message": "reset successful"}

#get audio recording
@app.post("/post-audio/")
async def post_audio(file: UploadFile = File(...)):
    
    #get saved audio rb=read bytes
    # audio_input = open("voice.mp3", "rb")

    with open(file.filename, "wb") as buffer:
        buffer.write(file.file.read())
    audio_input = open(file.filename, "rb")

    #decode audio
    message_decoded = convert_audio_to_text(audio_input)

    # guard: warning if decode fails
    if not message_decoded:
        return HTTPException(status_code=400, detail="Failed to decode audio")
    
    #get response
    chat_response = get_chat_response(message_decoded)
    #print(chat_response)

    # guard: warning if chat response is not recieved
    if not chat_response:
        return HTTPException(status_code=400, detail="Failed to get chat response")

    #store messages
    store_messages(message_decoded, chat_response)

    #convert chat response to audio
    audio_output = convert_text_to_speech(chat_response)

    # guard: warning audio response from eleven labs fails
    if not audio_output:
        return HTTPException(status_code=400, detail="Failed to get eleven labs audio response")
    
    #create generator that yeilds chunks of data
    def iterfile():
        yield audio_output

    #return auido file
    return StreamingResponse(iterfile(), media_type="application/octet-stream")    

    print(message_decoded)

    return "DONE"

# # Post bot response; uploads video 
# # Note: not playing in browser when using post request
# @app.post("/post-audio/")
# async def post_audio(file: UploadFile = File(...)):
    
#     print("hello")

