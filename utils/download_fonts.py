import os.path as opath
from requests import get


url = 'https://www.ctan.org/tex-archive/fonts/cm/tfm'


font_names = open('font_names.txt').readlines()
for font_name in font_names:
    font_name = font_name.strip()
    source_url = '{}/{}'.format(url, font_name)
    print(font_name)
    destination_path = opath.join('fonts', font_name)
    with open(destination_path, 'wb') as file:
        response = get(source_url)
        file.write(response.content)
