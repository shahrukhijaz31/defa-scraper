import requests
import pymysql

from lxml import html


# Example usage:
host = 'localhost'
user = 'root'
password = ''
database = 'defa_db'

connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    cursorclass=pymysql.cursors.DictCursor
)

urls = [
    "https://www.defa.com/no/produkt-kategori/ladelosninger-elbil/",
    # "https://www.defa.com/no/produkt-kategori/ladere-og-invertere/",
    # "https://www.defa.com/no/produkt-kategori/bilalarm-sporing/",
    # "https://www.defa.com/no/produkt-kategori/bilvarme/"
]

products_urls = []
req = requests.get(urls[0])
root = html.fromstring(req.content)
products_urls.extend(root.xpath("//ul[contains(@class, 'products')]/li/a/@href"))

def return_if_exist(test_string):
    if len(test_string):
        return test_string[0].strip()
    return ""

def get_data_with_html_tags_using_xpath(data):
    data_with_tags = ""
    for element in data:
        tag = element.tag
        html_content = html.tostring(element, pretty_print=True).decode()
        html_desc = f"<{tag}>{html_content}</{tag}>"
        data_with_tags = "{}{}".format(data_with_tags, html_desc)

    return data_with_tags

def download_file(url, local_filename):
    try:
        # Send a GET request to the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Open a local file with write-binary mode
        with open("files/{}".format(local_filename), 'wb') as file:
            # Iterate over the content in chunks and write to the local file
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"File downloaded successfully to {local_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")

is_pagination = True
while is_pagination:

    products_urls.extend(root.xpath("//ul[contains(@class, 'products')]/li/a/@href"))
    is_pagination = root.xpath("//ul[@class='page-numbers']/li[last()]/a/@href")
    if len(is_pagination):
        is_pagination = is_pagination[0]
        req = requests.get(is_pagination)
        root = html.fromstring(req.content)

print("{} Urls found".format(len(products_urls)))

for url in products_urls:
    req = requests.get(url)
    root = html.fromstring(req.content)

    product_title = root.xpath("//h1[contains(@class, 'product_title')]/text()")[0]

    main_category_1 = return_if_exist(root.xpath("//nav[@class='woocommerce-breadcrumb']/a[1]/text()"))
    main_category_2 = return_if_exist(root.xpath("//nav[@class='woocommerce-breadcrumb']/a[2]/text()"))
    main_category_3 = return_if_exist(root.xpath("//nav[@class='woocommerce-breadcrumb']/a[3]/text()"))
    main_category_4 = return_if_exist(root.xpath("//nav[@class='woocommerce-breadcrumb']/a[4]/text()"))
    main_category_5 = return_if_exist(root.xpath("//nav[@class='woocommerce-breadcrumb']/a[5]/text()"))
    main_category_6 = product_title

    product_id = return_if_exist(root.xpath("//span[@class='sku']/text()"))
    product_price = return_if_exist(root.xpath("//div[@class='price-wrap']/span/bdi/text()"))
    

    product_introduction = return_if_exist(root.xpath("//h1[contains(@class, 'product_title')]/following-sibling::div[@class='subtitle']/text()"))
    product_description = return_if_exist(root.xpath("//div[contains(@class, 'woocommerce-product-details__short-description')]/p/text()"))

    product_description = "{} {}".format(product_introduction, product_description)

    files = root.xpath("//div[@id='downloads']/div[@class='content']/a")
    attachements = []
    cursor = connection.cursor()

    for file in files:
        source = file.xpath("@href")[0]
        name = source.split("/")[-1]
        download_file(source, name)

        attachements.append({
            "name": name,
            "pdfs": source
        })

        # INSERT INTO `defa_product_files`(`id`, `product_id`, `source`, `created_at`)
        insert_files_query = "INSERT INTO defa_product_files (`product_id`, `source`, `name`) VALUES ('%s', '%s', '%s')"
        cursor.execute(insert_files_query  % (product_id, url, name))
        connection.commit()
                              
    product_description = get_data_with_html_tags_using_xpath(
        root.xpath("//div[contains(@class,'desc product-section')]/div[@class='content']")
        )

    product_specification = get_data_with_html_tags_using_xpath(
        root.xpath("//div[contains(@class,'specs product-section')]/div[@class='content']")
    )

    

    images = ""
    for image in root.xpath("//div[@class='woocommerce-product-gallery__image']/a/img/@data-large_image"):
        images = "{}, {}".format(images, image)

    insert_query = "INSERT INTO defa_product (title, price, introduction, product_id, main_category_2, main_category_3, main_category_4, main_category_5, main_category_6, specification, description, source_url, images) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
    cursor.execute(insert_query  % (product_title, product_price, product_description, product_id, main_category_2, main_category_3, main_category_4, main_category_5, main_category_6, product_specification, product_description, url, images))
    connection.commit()

    print("{} -- Scraped".format(product_id))
