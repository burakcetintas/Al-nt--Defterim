from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

# Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim", validators=[validators.Length(min=2, max=15)])
    surname = StringField("Soy İsim", validators=[validators.Length(min=2, max=15)])
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min=2, max=15)])
    password = PasswordField("Parola", validators=[

        validators.DataRequired(message= "Lütfen bir parola belirleyin!"),
        validators.EqualTo(fieldname= "confirm",message="Parolanız uyuşmuyor!")

    ])
    confirm = PasswordField("Parolayı Doğrula")

# Giriş formu
class LoginForm(Form):
    username= StringField("Kullanıcı Adı")
    password= PasswordField("Parola")


app = Flask(__name__)
app.secret_key= "alintidefterim"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "alintidefterim"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

#kitaplar kısmı
@app.route("/books")
def books():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From book"
    result = cursor.execute(sorgu)

    if result > 0:
        books = cursor.fetchall()

        return render_template("books.html", books = books)
    else:
        return render_template("books.html")


#defter kısmı
@app.route("/dashboard")
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From book where ekleyen = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        book = cursor.fetchall()
        return render_template("dashboard.html", book = book)
    else:
        return render_template("dashboard.html")

# kayıt olma kısmı
@app.route("/register",methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        surname = form.surname.data
        username = form.username.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,surname,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,surname,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla kayıt oldunuz...", "success")


        return redirect(url_for("login"))

    else:
        return render_template("register.html", form = form )


#giriş yapma işlemi
@app.route("/login", methods= ["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s "
        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız...","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdini...","danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullanıcı bulunmamaktadır...", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form = form)

# çıkış işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# kitap ekleme
@app.route("/addbook", methods = ["GET","POST"])
def addbook():
    form = BookForm(request.form)

    if request.method == "POST":
        name = form.name.data
        author = form.author.data
        content = form.content.data


        cursor = mysql.connection.cursor()
        sorgu = "Insert into book(name, author, content, ekleyen) VAlUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,author,content,session["username"] ))
        mysql.connection.commit()
        cursor.close()

        flash("Kitap başarıyla eklendi...", "success")

        return redirect(url_for("dashboard"))

    return render_template("addbook.html",form = form)

@app.route("/delete/<string:id>")
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from book where id = %s"
    result = cursor.execute(sorgu,(id))

    if result > 0:
        sorgu2 = "Delete from book where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))


    else:
        return redirect(url_for("index"))

#kitap form
class BookForm(Form):
    name = StringField("Kitap İsmi")
    author = StringField("Yazar")
    content =  TextAreaField("Alıntılar")

@app.route("/book/<string:id>")
def book(id):
    try:
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM book WHERE id = %s"
        result = cursor.execute(sorgu, (id,))

        if result > 0:
            book = cursor.fetchone()
            return render_template("book.html", book=book)
        else:
            return render_template("book.html", book=None)
    except Exception as e:
        return f"Hata: {e}"
    finally:
        cursor.close()



if __name__ == "__main__":
    app.run(debug=True)