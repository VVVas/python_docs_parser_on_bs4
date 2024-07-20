# Парсер документации Python для командной строки  

## Режимы работы парсера задаётся обязательным позиционным аргументом  

whats-new — ссылки на документы «Что нового?» для каждой версии.  
latest-versions — ссылки на документацию для каждой версии и её статус.  
download — скачать документацию в pdf для последней версии.  
pep — количество PEP каждого статуса.  

## Необязательные именованные аргументы
-h, --help — краткая справка по использованию парсера.  
-c, --clear-cache — очистка кеша.  
-o, --output — дополнительные способы вывода данных:  
    pretty — в командную строку с форматированием,  
    file — в csv файл.  

## Как развернуть  

Создать окружение  
```  
python -m venv venv  
```  

Активировать окружение, обновить pip и установить зависимости  
```  
source venv/Scripts/activate  
python -m pip install --upgrade pip  
pip install -r requirements.txt  
```  

Запустить с неодходиммыми аргументами  
```  
python src/main.py whats-new   
```  

По окончании использования деактивировать окружение  
```  
deactivate  
```  

## Стек технологий  
Python, BeautifulSoup4  

[Мишустин Василий](https://github.com/vvvas), v@vvvas.ru  
