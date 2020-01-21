from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db['Users']

def Userexist(username):
    if users.find({'Username': username}).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']

        if Userexist(username):
            retJson = {
                'status': 301,
                'message': 'Invalid Username'
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            'Username': username,
            'Password': hashed_pw,
            'Tokens': 6
        })

        retJson = {
            'status': 200,
            'message': 'You have successfuly Registered to the API'
        }
        return jsonify(retJson)


class Login(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']


        if Userexist(username):
            retJson4 = {
                'message':'user logged in successfully',
                'status':200
            }
            return jsonify(retJson4)

def verifypw(username, password):
    if not Userexist(username):
        return False

    hashed_pw = users.find({
        'Username':username,
    })[0]['Password']

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        'Username':username
    })[0]['Tokens']
    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']
        text1 = postedData['text1']
        text2 = postedData['text2']

        if not Userexist(username):
            retJson = {
                'status': 301,
                'message': 'Invalid Username'
            }
            return jsonify(retJson)

        correct_pw = verifypw(username, password)

        if not correct_pw:
            retJson = {
                'status':302,
                'message':'invalid Password'
            }

        num_tokens = countTokens(username)

        if num_tokens <= 0:
            retJson = {
                'status':303,
                'message':'You are out of Token, Please fill it out!'
            }

            return jsonify(retJson)

        #calculate the edit distance
        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        #ratio is a number between 0 and 1 the closer to 1,
        #the more similar text1 and text2 add_resource

        ratio = text1.similarity(text2)

        retJson = {
            'status':200,
            'similarity': ratio,
            'message':'Similarity score calculated successfully'
        }

        current_token = countTokens(username)
        users.update({
            'Username':username,
        },{
            '$set':{
                'Tokens':current_token - 1
            }
        })
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['admin_pw']
        refill_amount = postedData['refill']

        if not Userexist(username):
            retJson = {
                'status':301,
                'message':'Invalid Username'
            }
            return jsonify(retJson)

        correct_pw = "123asd"
        if not password == correct_pw:
            retJson = {
                'status':304,
                'message':'Invalid Admin password'
            }

        current_token = countTokens(username)
        users.update({
            'Username':username
        },{
            '$set':{
                'Tokens': refill_amount + current_token
            }
        })
        retJson = {
            'status':200,
            'message':'Token Refilled Successfully'
        }

api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')
api.add_resource(Login, '/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
