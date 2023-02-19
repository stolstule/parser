import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import Error
from transliterate import translit

count = 0
def get_url():
    for page in range(1, 5):
        url = f'https://www.labirint.ru/genres/2788/?page={page}'
        responce = requests.get(url)
        soup = BeautifulSoup(responce.text, 'lxml')
        data_all = soup.find_all('div', class_='relative product-cover__relative')

        for i in range(40, len(data_all)):
            card_url = 'https://www.labirint.ru' + data_all[i].find('a', class_='cover').get('href')
            yield card_url
        print(f'страница-{page}')


id_category = 3 # НЕ ЗАБЫТЬ, СМЕНА КАТЕГОРИИ ВАЖНА11



connection = psycopg2.connect(user="stolstule",
                              # пароль, который указали при установке PostgreSQL
                              password="bookerpass",
                              host="127.0.0.1",
                              port="5432",
                              database="book_shop")
cursor = connection.cursor()

# cursor.execute(f"SELECT * FROM store_book WHERE slug='{'grsh'}'")
# print(type(cursor.fetchall()[0][0]))

for card_url in get_url():
    responce = requests.get(card_url)
    soup = BeautifulSoup(responce.text, 'lxml')
    data = soup.find('div', id='product')
    img = data.find('div', id='product-image').find('img', class_='book-img-cover').get('data-src')
    title = data.find('div', id='product-title').find('h1').text
    title = title[title.find(':') + 1:].strip().replace("'", "`")
    try:
        price = data.find('span', class_='buying-pricenew-val-number').text.strip()
    except:
        price = data.find('span', class_='buying-price-val-number').text.strip()
    else:
        price = data.find('span', class_='buying-pricenew-val-number').text.strip()

    try:
        author = data.find('div', class_='authors').find('a', class_='analytics-click-js').text
    except:
        author = 'Неизвестно'
    else:
        author = data.find('div', class_='authors').find('a', class_='analytics-click-js').text
    publisher = data.find('div', class_='publisher').find('a', class_='analytics-click-js').text.replace("'", "`")
    isbn = data.find('div', class_='isbn').text.split()
    isbn = " ".join(isbn[:2])
    try:
        description = data.find('div', id='product-about').find('p').text
    except:
        continue
    else:
        description = data.find('div', id='product-about').find('p').text.replace("'", "`")

    try:
        volume = data.find('div', class_='pages2').text.split()[1]
    except:
        volume = 0
    else:
        volume = data.find('div', class_='pages2').text.split()[1]
    slug = translit(title, language_code='ru', reversed=True).replace("'", "")
    table_query = f"INSERT INTO store_book (TITLE, ISBN, PRICE, IMAGE, VOLUME, DESCRIPTION, AUTHOR, PUBLISHER, SLUG) VALUES('{title}', '{isbn}', '{int(price)}', '{img}', '{int(volume)}', '{description}', '{author}', '{publisher}', '{slug}')"

    cursor.execute(f"SELECT * FROM store_book WHERE slug='{slug}'")
    povtor = cursor.fetchall()

    if len(povtor) > 0:
        id_book = povtor[0][0]
        cursor.execute(f"SELECT * FROM store_book_category WHERE book_id = {id_book} AND category_id = {id_category}")
        peresechenie = cursor.fetchall()
        if len(peresechenie) > 0:
            print("Пересечение уже есть")
            continue
        else:
            cursor.execute(f"INSERT INTO store_book_category (book_id, category_id) VALUES ({id_book}, {id_category})")
            print("Книга уже есть")
            continue
    else:
        cursor.execute(table_query)
        connection.commit()
        cursor.execute(f"SELECT * FROM store_book WHERE slug='{slug}'")
        id_book = cursor.fetchall()[0][0]
        cursor.execute(f"INSERT INTO store_book_category (book_id, category_id) VALUES ({id_book}, {id_category})")

    connection.commit()
    cursor.execute(f"SELECT * FROM store_book WHERE slug='{slug}'")
    print(cursor.fetchall())
    count += 1
    print(f"{count} запись успешно вставлена")

cursor.close()
connection.close()
count = 0

