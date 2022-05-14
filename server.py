import bcrypt
import psycopg2
import setup
from flask import Flask
from flask_restful import Resource,Api
from uuid import uuid4

"""Connect to db (localhost)""" 
con = psycopg2.connect(
    host = 'db',
    user = 'postgres',
    password = 'password',
    port = '5432',
    database = 'SummitDB'
)

def updatePersonTraining(training_id,person_id):
    """Gets training id (INT) and person id (INT) and updates training to include person and person to include training"""
    cur = con.cursor()

    training_id_str = "',"+str(training_id)+"'"
    cur.execute(
        "UPDATE Person_table SET training =CONCAT( Person_table.training , "+training_id_str+" ) WHERE id ="+str(person_id)+";"
    )
    con.commit()

    cur = con.cursor()
    person_id_str = "',"+str(person_id)+"'"
    cur.execute(
        "UPDATE Training_Table SET Person =CONCAT( Training_Table.person , "+person_id_str+" ) WHERE id ="+str(training_id)+";"
    )
    con.commit()

def updateRemovePersonTraining(training_id,person_id):
    """Removes person from training and training from person"""
    #Update Training Table
    cur = con.cursor()
    cur.execute(
        "SELECT PERSON FROM TRAINING_TABLE WHERE id ="+str(training_id)+" ;"
    )
    data=cur.fetchall()
    persons = data[0][0].split(',')
    persons.remove(str(person_id))
    persons = ','.join(persons)
    cur = con.cursor()
    cur.execute(
        "UPDATE Training_Table SET Person ='"+persons+"' WHERE id ="+str(training_id)+";"
    )
    con.commit()
    #Update Person Table
    cur = con.cursor()
    cur.execute(
        "SELECT Training FROM Person_TABLE WHERE id ="+str(person_id)+" ;"
    )
    data=cur.fetchall()
    trainings=data[0][0].split(',')
    trainings.remove(str(training_id))
    trainings = ','.join(trainings)
    cur = con.cursor()
    cur.execute(
        "UPDATE person_Table SET training ='"+trainings+"' WHERE id ="+str(person_id)+";"
    )
    con.commit()

def getAttendance(training_id):
    """Returns full names of people who came to the training by id(INT)"""
    cur = con.cursor()
    cur.execute(
        "SELECT PERSON FROM TRAINING_TABLE WHERE id ="+str(training_id)+" ;"
    )
    data=cur.fetchall()
    people=""
    for d in data:
        people+=str(d)+','
    # Some lines to insure sql syntax is correct
    people=people.rstrip(',').rstrip(')').rstrip(',').rstrip("'")+')'
    people="("+people.lstrip('(').lstrip("'").lstrip(',')
    if people=="()":
        return [""]
    cur = con.cursor()
    cur.execute(
        "SELECT F_NAME,L_NAME,ID FROM Person_TABLE WHERE id in "+people+";"
    )
    data = cur.fetchall()
    result = []
    for row in data:
        result.append(str(row[0])+" "+str(row[1])+" "+str(row[2]))
    return result

def getTrainings(person_id):
    """Returns coach name and date of all trainings by person id(INT)"""
    cur = con.cursor()
    cur.execute(
        "SELECT TRAINING FROM PERSON_TABLE WHERE id ="+str(person_id)+" ;"
    )
    data=cur.fetchall()
    training=""
    for d in data:
        training+=str(d)+','
    training=training.rstrip(',').rstrip(')').rstrip(',').rstrip("'")+')'
    training="("+training.lstrip('(').lstrip("'").lstrip(",")
    cur = con.cursor()
    cur.execute(
        "SELECT COACH,DATE FROM TRAINING_TABLE WHERE id in "+training+";"
    )
    data = cur.fetchall()
    trainings = []
    for row in data:
        trainings.append(str(row[0]+","+str(row[1])))
    return trainings

def login(username,password):
    """Checks if user and his password are valid, if they are returns the list of all persons, if not returns invalid msg"""
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM USER_TABLE WHERE username = '"+str(username)+"';"
    )
    data=cur.fetchall()
    if len(data)==0:
        return "Invalid"
    if not bcrypt.checkpw(password.encode(),data[0][1].encode()):
        return "Invalid"
    cur = con.cursor()
    cur.execute(
        "SELECT F_NAME,L_NAME,ID FROM PERSON_TABLE;"
    )
    data=cur.fetchall() 
    persons = []  
    for row in data:
        persons.append(str(row[0])+','+str(row[1])+','+str(row[2])) 
    return persons




def getTrainingIdByDateAndCoach(date,coach):
    """Returns training id if it exists for given date and coach, -1 if doesnt exist"""
    cur = con.cursor()
    cur.execute(
        "SELECT ID FROM TRAINING_TABLE WHERE date ='"+str(date)+"' AND coach = '"+coach+"';"
    )
    training_id=cur.fetchall()
    if len(training_id)==0:
        return -1
    return int(training_id[0][0])

def addTraining(coach,date):
    """Add training instance by coach and date"""
    cur = con.cursor()
    cur.execute(
        "INSERT INTO TRAINING_TABLE (COACH,DATE,PERSON,ID) VALUES ('"+coach+"','"+date+"','',nextval('Training_sequence'));"
    )
    con.commit()

def addUser(username,password):
    password = bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
    cur = con.cursor()
    cur.execute(
    f"""
    INSERT INTO USER_Table 
    (USERNAME,PASSWORD)
    VALUES('{username}','{password}')
    """ 
    )
    con.commit()

def addMember(firstName,lastName):
    cur = con.cursor()
    cur.execute(
    f"""
    INSERT INTO person_Table 
    (f_name,l_name,ID,training)
    VALUES('{firstName}','{lastName}',nextval('person_sequence'),'')
    """ 
    )
    con.commit()

def getPersonIdByName(firstName,lastName):
    cur = con.cursor()
    cur.execute(
        "SELECT ID FROM person_TABLE WHERE f_name ='"+firstName+"' AND l_name = '"+lastName+"';"
    )
    person_id=cur.fetchall()
    if len(person_id)==0:
        return -1
    return int(person_id[0][0])

def getAllTrainings():
    """Returns coach and date for all trainings that exist"""
    cur = con.cursor()
    cur.execute(
        "SELECT COACH,DATE FROM TRAINING_TABLE;"
    )
    data = cur.fetchall()
    trainings = []
    for row in data:
        trainings.append(str(row[0]+","+str(row[1])))
    return trainings

def authenticate(token):
    return token in activeTokens



class AddToTraining(Resource):
    """Updates all Persons to include the training and training to include all persons"""
    def get(self,persons,date,coach,token):    
        if not authenticate(token):
            return "Can't authenticate"
        persons = str(persons)
        training_id = getTrainingIdByDateAndCoach(date=date,coach=coach)
        # Training doesnt exist - happens if this is first time adding to the training
        if training_id==-1:
            addTraining(date=date,coach=coach)
            training_id = getTrainingIdByDateAndCoach(date=date,coach=coach)
        persons = persons.split(',')
        for person in persons:
            updatePersonTraining(training_id=int(training_id),person_id=int(person))

class GetAttendance(Resource):
    """Returns all persons who came to a training (by date and coach given)"""
    def get(self,date,coach,token):
        if not authenticate(token):
            return "Can't authenticate"
        training_id = getTrainingIdByDateAndCoach(date=date,coach=coach)
        if training_id==-1:
            addTraining(date=date,coach=coach)
            training_id = getTrainingIdByDateAndCoach(date=date,coach=coach)
        return getAttendance(training_id=int(training_id))

class GetTrainings(Resource):
    """Returns all trainings a person given has attended (coach and date)"""
    def get(self,person,token):
        if not authenticate(token):
            return "Can't authenticate"
        return getTrainings(person_id=int(person))   

class Login(Resource):
    """Checks if username and password exists, TRUE: returns persons list and token, FALSE: returns 'invalid'"""
    def get(self,username,password):
        result= login(username,password)
        if result == "Invalid":
            return result
        #Generate token for user
        token = str(uuid4())
        activeTokens.append(token)
        result.insert(0,token)
        return result

class RemoveFromTraining(Resource):
    """Removes training from persons and persons from training"""
    def get(self,persons,date,coach,token):
        if not authenticate(token):
            return "Can't authenticate"
        training_id = getTrainingIdByDateAndCoach(date=date,coach=coach)     
        persons = persons.split(',')
        for person in persons:
            updateRemovePersonTraining(training_id,person)

class AddUser(Resource):
    def get(self,username,password,token):
        if not authenticate(token):
            return "Can't authenticate"
        addUser(username,password)
        return "OK"


class AddMember(Resource):
    def get(self,firstName,lastName,token):
        if not authenticate(token):
            return "Can't authenticate"
        addMember(firstName=firstName,lastName=lastName)
        return getPersonIdByName(firstName,lastName)

class GetAllTrainings(Resource):
    def get(self,token):
        if not authenticate(token):
            return "Can't authenticate"
        return getAllTrainings()

class Logout(Resource):
    def get(self,token):
        if token in activeTokens:
            activeTokens.remove(token)

# Token list for authentication
activeTokens = []



app = Flask(__name__)
api = Api(app)

# Adding all routes to server functions
api.add_resource(AddToTraining,'/AddToTraining/<string:persons>/<string:date>/<string:coach>/<string:token>')
api.add_resource(GetAttendance,'/GetAttendance/<string:date>/<string:coach>/<string:token>')
api.add_resource(GetTrainings,'/GetTrainings/<string:person>/<string:token>')
api.add_resource(RemoveFromTraining,"/RemoveFromTraining/<string:persons>/<string:date>/<string:coach>/<string:token>")
api.add_resource(Login,'/Login/<string:username>/<string:password>')
api.add_resource(AddMember,'/AddMember/<string:firstName>/<string:lastName>/<string:token>')
api.add_resource(AddUser,'/AddUser/<string:username>/<string:password>/<string:token>')
api.add_resource(GetAllTrainings,'/GetAllTrainings/<string:token>')
api.add_resource(Logout,'/Logout/<string:token>')


if __name__=="__main__":
    if not setup.checkToSetup():
        setup.createTables()
        setup.createAdmin()
    app.run(debug=False,host='0.0.0.0')
