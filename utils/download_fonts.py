from requests import get  # to make GET request


def download(url, file_name):
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        response = get(url)
        # write to file
        file.write(response.content)

a = open('font_names.txt').readlines()
url = 'https://www.ctan.org/tex-archive/fonts/cm/tfm'
for li in a:
    li = li.strip()
    path = '{}/{}'.format(url, li)
    print(li)
    download(path, li)
