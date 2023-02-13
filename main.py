import requests
from bs4 import BeautifulSoup
from time import sleep
import psycopg2
from psycopg2 import Error
from transliterate import translit


def get_url():
    for i in range(1, 5):
        url = f'https://www.labirint.ru/genres/2498/?page={i}'
        responce = requests.get(url)
        soup = BeautifulSoup(responce.text, 'lxml')
        data_all = soup.find_all('div', class_='relative product-cover__relative')

        for i in range(40, len(data_all)):
            card_url = 'https://www.labirint.ru' + data_all[i].find('a', class_='cover').get('href')
            yield card_url

connection = psycopg2.connect(user="stolstule",
                              # пароль, который указали при установке PostgreSQL
                              password="bookerpass",
                              host="127.0.0.1",
                              port="5432",
                              database="book_shop")
cursor = connection.cursor()

count = 0

for card_url in get_url():
    responce = requests.get(card_url)
    soup = BeautifulSoup(responce.text, 'lxml')
    data = soup.find('div', id='product')
    img = data.find('div', id='product-image').find('img', class_='book-img-cover').get('data-src')
    title = data.find('div', id='product-title').find('h1').text
    title = title[title.find(':') + 1:].strip()
    price = data.find('span', class_='buying-pricenew-val-number').text.strip()
    try:
        author = data.find('div', class_='authors').find('a', class_='analytics-click-js').text
    except:
        author = 'Неизвестно'
    else:
        author = data.find('div', class_='authors').find('a', class_='analytics-click-js').text
    publisher = data.find('div', class_='publisher').find('a', class_='analytics-click-js').text
    isbn = data.find('div', class_='isbn').text.split()
    isbn = " ".join(isbn[:2])
    description = data.find('div', id='product-about').find('p').text
    try:
        volume = data.find('div', class_='pages2').text.split()[1]
    except:
        volume = 0
    else:
        volume = data.find('div', class_='pages2').text.split()[1]
    slug = translit(title, language_code='ru', reversed=True).replace("'", "")

    print(title, isbn, price, img, volume, author, publisher)
    table_query = f"INSERT INTO store_book (TITLE, ISBN, PRICE, IMAGE, VOLUME, DESCRIPTION, CATEGORY_ID, AUTHOR, PUBLISHER, SLUG) VALUES('{title}', '{isbn}', '{int(price)}', '{img}', '{int(volume)}', '{description}', '{1}', '{author}', '{publisher}', '{slug}')"
    cursor.execute(table_query)
    connection.commit()
    print("1 запись успешно вставлена")
    cursor.execute(f"SELECT * FROM store_book WHERE id={count}")
    record = cursor.fetchall()
    print("Результат", record)

cursor.close()
connection.close()

