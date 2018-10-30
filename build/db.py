import sqlite3

db = sqlite3.connect("crm.sqlite")

db.execute("DROP TABLE IF EXISTS Client")
db.execute("DROP TABLE IF EXISTS Article")
db.execute("DROP TABLE IF EXISTS Purchase")
db.execute("DROP TABLE IF EXISTS PurchaseList")
db.execute("DROP TABLE IF EXISTS Invoice")
db.execute("DROP TABLE IF EXISTS InvoiceList")

db.execute('''
CREATE TABLE Client (
    id int PRIMARY KEY,
    mail text,
    adrPHY text,
    adrLIV text,
    adrBILL text,
    nameSHOP text,
    namePERS text
)''')

db.commit()

db.execute('''
CREATE TABLE Purchase (
    id int,
    order_date date,
    mail_date date,
    client int,
    reference text,
    PRIMARY KEY(id, mail_date)
    FOREIGN KEY(client) REFERENCES Client(id)
)''')

db.execute('''
CREATE TABLE Article (
    id int PRIMARY KEY,
    description text,
    price int
)''')

db.execute('''
CREATE TABLE PurchaseList(
    order_id int,
    article_id int,
    quantity int,
    discount int,
    FOREIGN KEY(order_id) REFERENCES Purchase(id)
    FOREIGN KEY(article_id) REFERENCES Article(id)
)''')

db.execute('''
CREATE TABLE Invoice (
    id int PRIMARY KEY,
    order_date date,
    mail_date date,
    client int,
    reference text,
    FOREIGN KEY(client) REFERENCES Client(id)
)''')

db.execute('''
CREATE TABLE InvoiceList(
    order_id int,
    article_id int,
    quantity int,
    discount int,
    FOREIGN KEY(order_id) REFERENCES Purchase(id),
    FOREIGN KEY(article_id) REFERENCES Article(id)
)''')

db.commit()

db.close()
