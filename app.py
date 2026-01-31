import os
from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "faujihouse_secret"

def get_db():
    return sqlite3.connect(os.path.join(app.root_path, "database.db"))

def init_db():
    con = get_db()
    c = con.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY,
        name TEXT, rank TEXT, unit TEXT, room TEXT,
        checkin TEXT, checkout TEXT,
        days INTEGER, rate INTEGER,
        total INTEGER, advance INTEGER, balance INTEGER
    )""")

    if not c.execute("SELECT * FROM users").fetchone():
        c.execute("INSERT INTO users VALUES(NULL,'admin','admin')")

    con.commit()
    con.close()

init_db()

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u,p=request.form["username"],request.form["password"]
        con=get_db()
        user=con.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
        con.close()
        if user:
            session["user"]=u
            return redirect("/dashboard")
    return render_template("login.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session: return redirect("/")
    if request.method=="POST":
        f=request.form
        d1=datetime.strptime(f["checkin"],"%Y-%m-%d")
        d2=datetime.strptime(f["checkout"],"%Y-%m-%d")
        days=max((d2-d1).days,1)
        rate=int(f["rate"])
        adv=int(f["advance"])
        total=days*rate
        bal=total-adv

        con=get_db()
        con.execute("""INSERT INTO bookings
        (name,rank,unit,room,checkin,checkout,days,rate,total,advance,balance)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (f["name"],f["rank"],f["unit"],f["room"],f["checkin"],f["checkout"],
         days,rate,total,adv,bal))
        con.commit()
        con.close()
        return redirect("/bookings")
    return render_template("dashboard.html")

# ---------- BOOKINGS ----------
@app.route("/bookings")
def bookings():
    if "user" not in session: return redirect("/")
    con=get_db()
    data=con.execute("SELECT * FROM bookings").fetchall()
    summary=con.execute("""
        SELECT SUM(total), SUM(advance), SUM(balance) FROM bookings
    """).fetchone()
    con.close()
    return render_template("bookings.html",data=data,summary=summary)

# ---------- EDIT ----------
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    if "user" not in session: return redirect("/")
    con=get_db()
    if request.method=="POST":
        f=request.form
        d1=datetime.strptime(f["checkin"],"%Y-%m-%d")
        d2=datetime.strptime(f["checkout"],"%Y-%m-%d")
        days=max((d2-d1).days,1)
        rate=int(f["rate"])
        adv=int(f["advance"])
        total=days*rate
        bal=total-adv

        con.execute("""UPDATE bookings SET
        name=?,rank=?,unit=?,room=?,checkin=?,checkout=?,
        days=?,rate=?,total=?,advance=?,balance=? WHERE id=?""",
        (f["name"],f["rank"],f["unit"],f["room"],f["checkin"],f["checkout"],
         days,rate,total,adv,bal,id))
        con.commit()
        con.close()
        return redirect("/bookings")

    row=con.execute("SELECT * FROM bookings WHERE id=?",(id,)).fetchone()
    con.close()
    return render_template("edit.html",r=row)

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session: return redirect("/")
    con=get_db()
    con.execute("DELETE FROM bookings WHERE id=?",(id,))
    con.commit()
    con.close()
    return redirect("/bookings")

# ---------- RECEIPT ----------
@app.route("/receipt/<int:id>")
def receipt(id):
    con=get_db()
    r=con.execute("SELECT * FROM bookings WHERE id=?",(id,)).fetchone()
    con.close()
    return render_template("receipt.html",r=r)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )


