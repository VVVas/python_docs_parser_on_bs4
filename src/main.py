"""Парсер документации Python для командной строки."""
import logging
import os
import re
from urllib.parse import urljoin, urlparse

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, MAIN_PEP_URL
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    """Ссылки на документы «Что нового?» для каждой версии."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    response = get_response(session, whats_new_url)
    if response is None:
        logging.info(f'Получен пустой ответ при запросе {whats_new_url}')
        return None

    soup = BeautifulSoup(response.text, features='lxml')

    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        name='li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        response = get_response(session, version_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features='lxml')

        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')

        dl_text = dl.text.replace('\n', ' ')

        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):
    """Ссылки на документацию для каждой версии и её статус."""
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        logging.info(f'Получен пустой ответ при запросе {MAIN_DOC_URL}')
        return None

    soup = BeautifulSoup(response.text, features='lxml')

    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})

    ul_tags = sidebar.find_all(name='ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]

    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']

        text_match = re.search(pattern, a_tag.text)

        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''

        results.append(
            (link, version, status)
        )

    return results


def download(session):
    """Скачивание документации в pdf для последней версии."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    response = get_response(session, downloads_url)
    if response is None:
        logging.info(f'Получен пустой ответ при запросе {downloads_url}')
        return

    soup = BeautifulSoup(response.text, features='lxml')

    main_tag = find_tag(soup, 'div', attrs={'role': 'main'})
    table_tag = find_tag(main_tag, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )

    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)

    parsed_archive_url = urlparse(archive_url)
    archive_url_path = parsed_archive_url.path
    _, filename = os.path.split(archive_url_path)

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)
    if response is None:
        logging.info(f'Получен пустой ответ при запросе {archive_url}')
        return

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    """Количество PEP каждого статуса."""
    pep_url = urljoin(MAIN_PEP_URL, '')

    response = get_response(session, pep_url)
    if response is None:
        logging.info(f'Получен пустой ответ при запросе {pep_url}')
        return None

    soup = BeautifulSoup(response.text, features='lxml')

    section = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tbody_tag = find_tag(section, 'tbody')
    tr_tags = tbody_tag.find_all(
        name='tr', attrs={'class': re.compile(r'row-(even|odd)')}
    )

    status_mismatch = ['\nНесовпадающие статусы:\n']
    status_counts = {}

    for tr_tag in tqdm(tr_tags):
        status_key_abbr_tag = find_tag(tr_tag, 'abbr')
        status_key = status_key_abbr_tag.text[1:]
        pep_link_a_tag = find_tag(
            tr_tag, 'a', attrs={'class': 'pep reference internal'}
        )
        pep_link = urljoin(pep_url, pep_link_a_tag['href'])

        response_pep = get_response(session, pep_link)
        if response_pep is None:
            continue

        pep_soup = BeautifulSoup(response_pep.text, features='lxml')
        dl_tag = find_tag(
            pep_soup, 'dl', attrs={'class': 'rfc2822 field-list simple'}
        )
        status_abbr_tag = find_tag(dl_tag, 'abbr')
        status = status_abbr_tag.text

        if status not in EXPECTED_STATUS[status_key]:
            status_mismatch.append(
                f'{pep_link}\nВ карточке: {status}\n'
                f'Ожидаемые: {EXPECTED_STATUS[status_key]}\n'
            )

        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1

    if len(status_mismatch) > 1:
        logging.info('\n'.join(status_mismatch))

    results = [('Статус', 'Количество')]
    results.extend(status_counts.items())
    results.append(('Total', sum(status_counts.values())))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    """Запуск парсера."""
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode

    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
