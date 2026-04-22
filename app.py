from flask import Flask,request,url_for,redirect,render_template,flash,session,send_file
from flask_session import Session
from otp import generateotp
# import flask_excel as excel
from flask import Response
import csv
import io
import os
import re
from stoken import endata,dndata
from cmail import send_mail
from io import BytesIO
import mysql.connector 
# mydb=mysql.connector.connect(user='root',host='localhost',password='root',database='snm',)
from mysql.connector import connection

try:
    mydb = connection.MySQLConnection(
        host="localhost",
        user="root",
        password="nandu@2003",
        database="snm",
        port=3306
    )
    print("✅ Database connected successfully!")
except Exception as e:
    print("❌ Connection to database failed:", e)


app=Flask(__name__)
# excel.init_excel(app)
# app.secret_key='code9'
app.secret_key="b'\x08S'"

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
@app.route('/')  
def home():
    return render_template('welcome.html')
@app.route('/register',methods=['GET','POST']) 
def register():
    if request.method=='POST':
        username=request.form['uname']
        useremail=request.form['uemail']
        userpassword=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from users where useremail=%s',[useremail])
            count_email=cursor.fetchone() #(1,) or (0,)
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not verify email')
            return redirect(url_for('register'))
        else:
            if count_email[0]==0:
                server_otp=generateotp()
                # return server_otp
                userdata={'username':username,'usermail':useremail,'userpassword':userpassword,'server_otp':server_otp}
                subject='OTP for SNM_APP'
                body=f'use the given otp for user registration {server_otp}'
                send_mail(to=useremail,subject=subject,body=body)
                # return 'otp has sent mail'
                flash('OTP has been sent to given mail')
                return redirect(url_for('otpverify',var_data=endata(data=userdata)))
            elif count_email[0]==1:
                flash('Email already existed')

    return render_template('register.html')
@app.route('/otpverify/<var_data>',methods=['GET','POST'])
def otpverify(var_data):
    if request.method=='POST':
        user_otp=request.form['userotp']
        try:
            user_data=dndata(var_data)  #{'username':username,'usermail':usermail,'userpassword':userpassword,'server_otp':server_otp}
        except Exception as e:
            print(e)
            flash('could not verify otp please try again')
            return redirect(url_for('register'))
        else:
            if user_data['server_otp']==user_otp:
                #database
                cursor=mydb.cursor()
                cursor.execute('insert into users(username,useremail,userpassword) values(%s,%s,%s)',[user_data['username'],user_data['useremail'],user_data['userpassword']])
                mydb.commit()
                flash('user details stored')
                return redirect(url_for('login'))

                # return 'Success'
            else:
                flash('otp was wrong')
                
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        login_useremail=request.form.get('email').strip()  #strip() extra spaces unte pothayi
        login_password=request.form.get('password').strip()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from users where useremail=%s',[login_useremail])
            count_email=cursor.fetchone()   #(1,) or (0,)
            # cursor.close()
        except Exception as e:
            print(e)
            flash('Could not connect to db')
            return redirect(url_for('login'))
        else:
            if count_email[0]==1:
                cursor.execute('select userpassword from users where useremail=%s',[login_useremail])
                stored_password=cursor.fetchone() #(123,)
                cursor.close()
                if stored_password[0]==login_password:
                    flash('Login Successfully')
                    session['user']=login_useremail  #session loki velli store ayyiddi
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid password')
                    return redirect(url_for('login'))
            else:
                flash('User not found')
            


    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('pls login to get dashboard')
        return redirect(url_for('login'))
    
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form.get('title').strip()
            notesContent=request.form.get('content').strip()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone()
                if user_id:
                    cursor.execute('insert into notesdata(notestitle,notescontent,userid) values(%s,%s,%s)',[title,notesContent,user_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    print(user_id)
                    flash('user not verified')
                    return redirect(url_for('addnotes'))
            except Exception as e:
                print(e)
                flash('Could not notes')
                return redirect(url_for('addnotes'))
            else:
                flash('Notes added successfully')



        return render_template('addnotes.html')
    else:
        flash('pls login to add notes')
        return redirect(url_for('login'))
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from notesdata where userid=%s',[user_id[0]])
                notesdata=cursor.fetchall() #[(1,'python','programming language'),(2,...)]
            else:
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',notesdata=notesdata)

    else:
        flash('pls login to view all notes')
        return redirect(url_for('login'))

@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from notesdata where userid=%s and notesid=%s',[user_id[0],nid])
                notesdata=cursor.fetchone() #((1,'python','programming language'),)
            else:
                print(e)
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',notesdata=notesdata)

    else:
        flash('pls login to view all notes')
        return redirect(url_for('login'))
    
@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('delete from notesdata where userid=%s and notesid=%s',[user_id[0],nid])
                mydb.commit() #cmplete ga data save ayyiddi
                cursor.close()

            else:
                print(e)
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
            flash('Notes delete successfully')
            return redirect(url_for('viewallnotes'))

    else:
        flash('pls login to view all notes')
        return redirect(url_for('login'))
    
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from notesdata where userid=%s and notesid=%s',[user_id[0],nid])
                notesdata=cursor.fetchone() #((1,'python','programming language'),)
            else:
                print(e)
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
            if request.method=='POST':
                updated_title=request.form['title']
                updated_content=request.form['content']
                try:
                    cursor.execute('update notesdata set notestitle=%s,notescontent=%s where notesid=%s and userid=%s',[updated_title,updated_content,nid,user_id[0]])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('could not update notesdata')
                    return redirect(url_for('updatenotes',nid=nid))
                else:
                    flash('Notes updated successfully')
                    return redirect(url_for('viewallnotes',nid=nid))
            return render_template('updatenotes.html',notesdata=notesdata)
        
    else:
        flash('pls login to update notes')
        return redirect(url_for('login'))


@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('select * from notesdata where userid=%s',[user_id[0]])
                notesdata=cursor.fetchall()
                
                if not notesdata:
                    flash('No notes found')
                    return redirect(url_for('viewallnotes'))
                    
                array_data=[list(i) for i in notesdata]
                columns=['Notesid','Title','Content','Userid','Time']
                array_data.insert(0,columns)
                
                cursor.close()
                
              
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(array_data[0])  
                for row in array_data[1:]:      
                    writer.writerow(row)
                
                return Response(
                    output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=notesdata.csv"}
                )
            else:
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch notes data')
            return redirect(url_for('dashboard'))
    else:
        flash('pls login')
        return redirect(url_for('login'))

@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            fileobj=request.files['file']
            filedata=fileobj.read()
            fname=fileobj.filename
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone()
                cursor.execute('select count(*) from filesdata where filename=%s',[fname])
                filecount=cursor.fetchone()
                
                if user_id:
                    if filecount[0]==0:
                        cursor.execute('insert into filesdata(filename,filecontent,userid) values(%s,%s,%s)',[fname,filedata,user_id[0]])
                        mydb.commit()
                        cursor.close()
                    else:
                        flash('file already existed')
                        return redirect(url_for('uploadfile'))
                else:
                    flash('could not verify user')
                    return redirect(url_for('uplaodfile'))
            except Exception as e:
                print(e)
                flash('could not uplaod file')
                return redirect(url_for('uplaodfile'))
            else:
                flash('File upload successfully')

            
        return render_template('uploadfile.html')
    else:
        flash('pls login upload a file')
        return  redirect(url_for('login'))

@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from filesdata where userid=%s',[user_id[0]])
                filesdata=cursor.fetchall() #[(1,'python','programming language'),(2,...)]
            else:
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch files data')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallfiles.html',filesdata=filesdata)

    else:
        flash('pls login to view all notes')
        return redirect(url_for('login'))
    
@app.route('/viewfile/<fid>') #view==reading method
def viewfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from filesdata where userid=%s and fileid=%s',[user_id[0],fid])
                file_data=cursor.fetchone() #[(1,'python','programming language'),(2,...)]
            else:
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch files data')
            return redirect(url_for('dashboard'))
        else:
            byte_array=BytesIO(file_data[2])
            return send_file(byte_array,download_name=file_data[1],as_attachment=False)
        
    else:
        flash('pls login to view file')
        return redirect(url_for('login'))
    
@app.route('/downloadfile/<fid>') #view==reading method
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from filesdata where userid=%s and fileid=%s',[user_id[0],fid])
                file_data=cursor.fetchone() #[(1,'python','programming language'),(2,...)]
            else:
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not fetch files data')
            return redirect(url_for('dashboard'))
        else:
            byte_array=BytesIO(file_data[2])
            return send_file(byte_array,download_name=file_data[1],as_attachment=True)
        
    else:
        flash('pls login to view file')
        return redirect(url_for('login'))

@app.route('/deletefile/<fid>')
def deletefile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('delete from filesdata where userid=%s and fileid=%s',[user_id[0],fid])
                mydb.commit() #cmplete ga data save ayyiddi
                cursor.close()

            else:
                print(e)
                flash('could not verify email')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Could not delete file data')
            return redirect(url_for('dashboard'))
        else:
            flash('file delete successfully')
            return redirect(url_for('viewallfiles'))

    else:
        flash('pls login to view all notes')
        return redirect(url_for('login'))
@app.route('/search', methods=['POST'])
def search():
    if not session.get('user'):
        flash('Please login to search')
        return redirect(url_for('login'))

    search_data = request.form.get('search_value', '').strip()

    # Allow only letters, numbers and spaces
    pattern = re.compile(r'^[A-Za-z0-9 ]+$')

    if not search_data or not pattern.match(search_data):
        flash('Invalid search input')
        return redirect(url_for('dashboard'))

    try:
        cursor = mydb.cursor(buffered=True)

        cursor.execute(
            'SELECT userid FROM users WHERE useremail=%s',
            (session.get('user'),)
        )
        user_id = cursor.fetchone()

        if not user_id:
            flash('User not found')
            return redirect(url_for('dashboard'))

        cursor.execute(
            '''
            SELECT * FROM notesdata
            WHERE userid=%s AND notestitle LIKE %s
            ''',
            (user_id[0], search_data + '%')
        )

        search_result = cursor.fetchall()

        return render_template(
            'viewallnotes.html',
            notesdata=search_result
        )

    except Exception as e:
        print(e)
        flash('Could not fetch notes data')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('pls login to logout')
        return redirect(url_for('login'))
if __name__ == "__main__":
    app.run()