import logging
import os
import re
from urllib.parse import urljoin, urlparse

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL
# Добавьте к списку импортов импорт функции с конфигурацией
# парсера аргументов командной строки.
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    # Вместо константы WHATS_NEW_URL, используйте переменную whats_new_url.
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    # Загрузка веб-страницы с кешированием.
    # session = requests_cache.CachedSession()
    # response = session.get(whats_new_url)
    # response.encoding = 'utf-8'
    response = get_response(session, whats_new_url)
    if response is None:
        # Если основная страница не загрузится, программа закончит работу.
        return

    # Печать текста всего ответа
    # print(response.text)

    # Создание "супа".
    soup = BeautifulSoup(response.text, features='lxml')

    # Шаг 1-й: поиск в "супе" тега section с нужным id. Парсеру нужен только
    # первый элемент, поэтому используется метод find().
    # main_div = soup.find(name='section', attrs={'id': 'what-s-new-in-python'})
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})

    # Шаг 2-й: поиск внутри main_div следующего тега div с классом toctree-wrapper.
    # Здесь тоже нужен только первый элемент, используется метод find().
    # div_with_ul = main_div.find(name='div', attrs={'class': 'toctree-wrapper'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})

    # Шаг 3-й: поиск внутри div_with_ul всех элементов списка li с классом toctree-l1.
    # Нужны все теги, поэтому используется метод find_all().
    sections_by_python = div_with_ul.find_all(name='li', attrs={'class': 'toctree-l1'})

    # Печать первого найденного элемента.
    # print(sections_by_python[0].prettify())

    # Инициализируйте пустой список results.
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        # Печать тегов a
        # print(version_a_tag)

        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        # Печать собранных ссылок каждой версии.
        # print(version_link)

        # Загрузите все страницы со статьями. Используйте кеширующую сессию.
        # response = session.get(version_link)
        # Укажите кодировку utf-8.
        # response.encoding = 'utf-8'

        response = get_response(session, version_link)
        if response is None:
            # Если страница не загрузится, программа перейдёт к следующей ссылке.
            continue

        # Сварите "супчик".
        soup = BeautifulSoup(response.text, features='lxml')
        # Найдите в "супе" тег h1.
        # h1 = soup.find(name='h1')
        h1 = find_tag(soup, 'h1')
        # Найдите в "супе" тег dl.
        # dl = soup.find(name='dl')
        dl = find_tag(soup, 'dl')

        # Добавьте в вывод на печать текст из тегов h1 и dl.
        # print(version_link, h1.text, dl.text)

        dl_text = dl.text.replace('\n', ' ')
        # На печать теперь выводится переменная dl_text — без пустых строчек.
        # print(version_link, h1.text, dl_text)

        # Добавьте в список ссылки и текст из тегов h1 и dl в виде кортежа.
        results.append(
            (version_link, h1.text, dl_text)
        )

    # # Печать списка с данными.
    # for row in results:
    #     # Распаковка каждого кортежа при печати при помощи звездочки.
    #     print(*row)
    return results


def latest_versions(session):
    # session = requests_cache.CachedSession()
    # response = session.get(MAIN_DOC_URL)
    # response.encoding = 'utf-8'
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    # sidebar = soup.find(name='div', attrs={'class': 'sphinxsidebarwrapper'})
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})

    ul_tags = sidebar.find_all(name='ul')

    # Печать всех найденных списков
    # print(ul_tags)

    # Перебор в цикле всех найденных списков.
    for ul in ul_tags:
        # Проверка, есть ли искомый текст в содержимом тега.
        if 'All versions' in ul.text:
            # Если текст найден, ищутся все теги <a> в этом списке.
            a_tags = ul.find_all('a')
            # Остановка перебора списков.
            break
        # Если нужный список не нашёлся,
        # вызывается исключение и выполнение программы прерывается.
        else:
            raise Exception('Ничего не нашлось')
    # print(a_tags)

    # Список для хранения результатов.
    results = [('Ссылка на документацию', 'Версия', 'Статус')]

    # Шаблон для поиска версии и статуса:
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    # Цикл для перебора тегов <a>, полученных ранее.
    for a_tag in a_tags:
        # Извлечение ссылки.
        link = a_tag['href']

        # Поиск паттерна в ссылке.
        text_match = re.search(pattern, a_tag.text)

        if text_match is not None:
            # Если строка соответствует паттерну,
            # переменным присываивается содержимое групп, начиная с первой.
            # version, status = text_match.groups()

            # мой вариант присвоения значений переменным
            version = text_match.group('version')
            status = text_match.group('status')
        else:
            # Если строка не соответствует паттерну,
            # первой переменной присваивается весь текст, второй — пустая строка.
            version, status = a_tag.text, ''

        # Добавление полученных переменных в список в виде кортежа.
        results.append(
            (link, version, status)
        )

    # # Печать результата.
    # for row in results:
    #     print(*row)
    return results


def download(session):
    # Вместо константы DOWNLOADS_URL, используйте переменную downloads_url.
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    # session = requests_cache.CachedSession()
    # response = session.get(downloads_url)
    # response.encoding = 'utf-8'
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    # main_tag = soup.find('div', attrs={'role': 'main'})
    main_tag = find_tag(soup, 'div', attrs={'role': 'main'})
    # table_tag = main_tag.find('table', attrs={'class': 'docutils'})
    table_tag = find_tag(main_tag, 'table', attrs={'class': 'docutils'})

    # print(table_tag)

    # Добавьте команду получения нужного тега.
    # pdf_a4_tag = table_tag.find('a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_tag = find_tag(table_tag, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')})

    # print(pdf_a4_tag)

    # Сохраните в переменную содержимое атрибута href.
    pdf_a4_link = pdf_a4_tag['href']
    # Получите полную ссылку с помощью функции urljoin.
    archive_url = urljoin(downloads_url, pdf_a4_link)

    print(archive_url)

    parsed_archive_url = urlparse(archive_url)
    archive_url_path = parsed_archive_url.path
    _, filename = os.path.split(archive_url_path)

    print(filename)

    # Сформируйте путь до директории downloads.
    downloads_dir = BASE_DIR / 'downloads'
    # Создайте директорию.
    downloads_dir.mkdir(exist_ok=True)
    # Получите путь до архива, объединив имя файла с директорией.
    archive_path = downloads_dir / filename

    # Загрузка архива по ссылке.
    response = session.get(archive_url)

    # В бинарном режиме открывается файл на запись по указанному пути.
    with open(archive_path, 'wb') as file:
        # Полученный ответ записывается в файл.
        file.write(response.content)

    # Допишите этот код в самом конце функции.
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    pep_url = urljoin(MAIN_PEP_URL, '')
    response = get_response(session, pep_url)
    if response is None:
        return
    # Пиши код!


# Скопируйте весь код ниже.
MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    # Запускаем функцию с конфигурацией логов.
    configure_logging()
    # Отмечаем в логах момент запуска программы.
    logging.info('Парсер запущен!')

    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()
    # Логируем переданные аргументы командной строки.
    logging.info(f'Аргументы командной строки: {args}')

    # Создание кеширующей сессии.
    session = requests_cache.CachedSession()
    # Если был передан ключ '--clear-cache', то args.clear_cache == True.
    if args.clear_cache:
        # Очистка кеша.
        session.cache.clear()
    # Получение из аргументов командной строки нужного режима работы.
    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)

    # Если из функции вернулись какие-то результаты,
    if results is not None:
        # передаём их в функцию вывода вместе с аргументами командной строки.
        control_output(results, args)
    # Логируем завершение работы парсера.
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
