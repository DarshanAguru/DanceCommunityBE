from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
from fastapi.responses import FileResponse
from utils.dbConnect import connectDB
from dbBaseModels.classes import Classes
from dbBaseModels.users import Users
from dbBaseModels.audition import Auditions
from dbBaseModels.institution import Institutions
from dbBaseModels.events import Events
from fastapi import Body, Request
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import uuid
import hashlib
import base64
from pathlib import Path
from utils.recommendations import getRecommendations
from typing import List
from bson.objectid import ObjectId



app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=uuid.uuid4())
origins = [
    "http://localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
db = connectDB()


#for debug and dev use case


@app.get('/')
def error():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@app.post('/register', response_model=Users)
async def register(req: Request, user: Users = Body(...)):
    try:
        if req.session.get('user', None) is not None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Already Logged In")
        users = db.users
        data = users.find_one({"email":user.email})
        if data is not None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Already Registered')
        userPass = hashlib.sha256(user.pswd.encode()).hexdigest()
        # user.userType = None
        id = str(users.insert_one({"name":user.name, "pswd":userPass,"type":user.type,"email": user.email,"phone":user.phone,"country":user.country, "city":user.city, "state":user.state, "clickTracks": []}).inserted_id)
        # user.userId = userId
        user.pswd = None
        user.id = id
        return user
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail =str(e))

@app.post('/login', response_model=Users)
async def login(req: Request, user: Users = Body(...)):
    try:
        if req.session.get('user', None) is not None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Already Logged In")
        password = hashlib.sha256(user.pswd.encode()).hexdigest()
        data = db.users.find_one({"email": user.email})
        if data is None:
            raise HTTPException(status_code=404, detail="Not Found")
        if password != data['pswd']:
            raise HTTPException(status_code=401, detail="Not Authorized")
        user.id = str(data['_id'])
        user.name = data['name']
        user.pswd = None
        user.email = data['email']
        user.phone = data['phone']
        user.type = data['type']
        user.country = data['country']
        user.state = data['state']
        user.city = data['city']
        user.clickTracks = data['clickTracks']
        req.session['user'] = str(user.id)
        return user
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail =str(e))


@app.post('/getRecs')
async def getRecs(req: Request):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userId = req.session.get('user', None)
        data = db.users.find_one({'_id': ObjectId(userId)})
        if(len(data['clickTracks']) > 2):
            return getRecommendations(userId)
        else:
            return {"message": "Can't Recommend"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



 # additional feature   
@app.post('/removeUser/{userId}')
async def removeUser(req: Request, userId: str):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        data = db.users.find_one_and_delete({'_id': ObjectId(userId)})
        if data is None:
            raise HTTPException(status_code=404, detail="Not Found")
        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post('/changePass/{userId}')
async def changePass(req: Request, userId: str , userPass: str = Body(...), userNewPass:str =  Body(...)):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        data = db.users.find_one({"_id": ObjectId(userId)})
        if data is None:
            raise HTTPException(status_code=404, detail="not found")
        password = hashlib.sha256(userPass.encode()).hexdigest()
        if password != data['pswd']:
            raise HTTPException(status_code=401, detail="Not Authorized")
        password = hashlib.sha256(userNewPass.encode()).hexdigest()
        db.users.update_one({"_id": ObjectId(userId)}, {"$set" : {"pswd":password}},  upsert=True)
        return {"message": "Password changed"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post('/logout')
async def logout(req: Request):
    try:
        if req.session.get('user',None) is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Not Logged In")
        req.session.pop('user',None)
        return {"message":"Logged Out"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@app.post('/addClass/{userId}', response_model=Classes)
async def addClass(req: Request, userId: str, clas : Classes = Body(...)):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userInfo = db.users.find_one({'_id': ObjectId(userId)})
        if userInfo is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        if userInfo['type'] == 'user':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        data_id = db.classes.insert_one({"userId": str(userId), "danceFormName": clas.danceFormName,"className":clas.className, "teacherName": clas.teacherName, "videoLink":clas.videoLink, "img": ""}).inserted_id
        clas.userId = str(userId)
        clas.id = str(data_id)
        return clas
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


   
@app.get('/getAllClasses', response_model=List[Classes])
async def getAllClasses(req: Request):
    try:
        classes = db.classes.find()
        classesList = []
        for row in classes:
            row['id'] = str(row['_id'])
            row['userId'] = str(row['userId'])
            classesList.append(Classes(**row))
        return classesList
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@app.post('/addClick/{classId}')
async def addClicks(req: Request, classId: str):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userId = req.session.get('user', None)
        data = db.users.find_one({'_id': ObjectId(userId)})
        if data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
        classData = db.classes.find_one({'_id': ObjectId(classId)})
        track = {"id": str(classId), "danceFormName": classData['danceFormName'], "className": classData['className']}
        total_tracks = []
        if data['clickTracks'] is None or []:
            total_tracks = [track]
        else:
            total_tracks = [*data['clickTracks'], track]
            db.users.update_one( {'_id': ObjectId(userId)}, { "$set" : {"clickTracks": total_tracks}}, upsert=True)
        return {"message": "click Saved"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get('/getImage/{path}')
async def getImage(req: Request, path: str):
    try:
        decpath = base64.b64decode(path.encode()).decode("utf-8")
        print(decpath)
        img = Path(decpath)
        if not img.is_file():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a File")

        return FileResponse(img)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post('/uploadFile/{type}/{id}')
async def uploadFile(req: Request,type: str, id: str, img: UploadFile | None = File(...)):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userId = str(req.session.get('user', None))
        userInfo = db.users.find_one({'_id': ObjectId(userId)})
        if userInfo is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        if userInfo['type'] == 'user':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        if img is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Not Found")
        path = base64.b64encode(f"statics/images/{type}/{id}A00A{img.filename}".encode()).decode()
        with open(f'statics/images/{type}/{id}A00A{img.filename}', "wb") as buffer:
            shutil.copyfileobj(img.file, buffer)
        if type == "auditions":
            db.auditions.update_one({"_id": ObjectId(id)}, {"$set": {"img": path}})
        elif type == "classes":
            db.classes.update_one({"_id": ObjectId(id)}, {"$set": {"img": path}})
        elif type == "events":
            db.events.update_one({"_id": ObjectId(id)}, {"$set": {"img": path}})
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid Type")
                        
        return {"message": "Uploaded Successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post('/addInstitution/{userId}', response_model=Institutions)
async def addInstitution(req: Request, userId: str, institution: Institutions = Body(...)):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userInfo = db.users.find_one({'_id': ObjectId(userId)})
        if userInfo is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        if userInfo['type'] == 'user':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        id = str(db.institutions.insert_one({"institutionName":institution.institutionName, "headOfInstitution":institution.headOfInstitution,"coursesOffered":institution.coursesOffered,"additionalOffers": institution.additionalOffers,"location":institution.location,"phone":institution.phone, "email":institution.email, "address":institution.address}).inserted_id)
        institution.id = id
        return institution
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@app.get('/getAllInstitutions', response_model=List[Institutions])
async def getAllClasses(req: Request):
    try:
        institutions = db.institutions.find()
        institutionsList = []
        for row in institutions:
            row['id'] = str(row['_id'])
            institutionsList.append(Institutions(**row))
        return institutionsList
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@app.post('/addAudition/{userId}', response_model=Auditions)
async def addAudition(req: Request, userId: str, audition: Auditions = Body(...)):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userInfo = db.users.find_one({'_id': ObjectId(userId)})
        if userInfo is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        if userInfo['type'] == 'user':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        id = str(db.auditions.insert_one({"title":audition.title, "requirements":audition.requirements,"date":audition.date,"additionalInfo": audition.additionalInfo,"location":audition.location,"phone":audition.phone, "email": audition.email, "address": audition.address, "img":""}).inserted_id)
        audition.id = id
        return audition
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@app.get('/getAllAuditions', response_model=List[Auditions])
async def getAllClasses(req: Request):
    try:
        auditions = db.auditions.find()
        auditionsList = []
        for row in auditions:
            row['id'] = str(row['_id'])
            auditionsList.append(Auditions(**row))
        return auditionsList
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@app.post('/addEvent/{userId}', response_model=Events)
async def addEvent(req: Request, userId: str, event: Events = Body(...)):
    try:
        if req.session.get('user', None) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        userInfo = db.users.find_one({'_id': ObjectId(userId)})
        if userInfo is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        if userInfo['type'] == 'user':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        id = str(db.events.insert_one({"title":event.title, "date":event.date,"timings": event.timings,"venue": event.venue,"img":""}).inserted_id)
        event.id = id
        return event
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get('/getAllEvents', response_model=List[Events])
async def getAllClasses(req: Request):
    try:
        events = db.events.find()
        eventsList = []
        for row in events:
            row['id'] = str(row['_id']) 
            eventsList.append(Events(**row))
        return eventsList
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=9000)
