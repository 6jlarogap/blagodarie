install-readme.txt
------------------

Установка Django проекта project на сервер Apache в Ubuntu Linux.
----------------------------------------------------------------

    (Здесь каталог app)

    * Полагаем:

        Пусть project - это:

            - имя проекта на github.com
                Полагаем, что проект там хранится. Возможен другой ресурс,
                например, bitbucket.org
            - имя каталога кода проекта
            - имя каталога медии проекта (загружаемых данных пользователями сайта):
                /home/www-data/django/MEDIA/project
            - имя базы данных проекта
            - имя сайта: project.org
            - каталог, где сертификаты на сайт https://project.org,
                /home/www-data/ssl-certificates/sslforfree/project.org/
              получаемые от https://www.sslforfree.com/
        
        - ~/venv/project:        
                                        virtual environment проекта.
                                        Пусть будет в домашнем каталоге установщика.

        - /home/www-data/django/project:
                                        код проекта

        - /home/www-data/django/MEDIA/project:
                                        медиа проекта (загружаемые пользователями данные)

        - USERNAME_GIT:                 имя пользователя на github.com:
                                        ресурсе, где хранится git копия проекта

        - USERNAME_LINUX                имя пользователя в ОС Linux

        - ubuntu:                       ubuntu server 18.04
 
    * Д.б. установлено на Linux:
        - средства разработки:
            * python3.6, не ниже:
                  * sudo apt install python3-all-dev
                  * sudo apt install python3-virtualenv python3-pycurl virtualenv

         - postgresql,
            * в т.ч. для разработчика:
              sudo apt install postgresql postgresql-server-dev-all
            полагаем, что используется база postgresql на localhost,
            в которой postgres- пользователь blagodarie будет владельцем
            базы данных blagodarieвсё дозволено. Это достигается в

            /etc/postgresql/<версия-postgresql>/main/

            добавлением строки в начале:
                local all blagodarie password
            с перезагрузкой postgresql (service postgresql restart)
            sudo -u postgres psql -U postgres
            CREATE USER blagodarie CREATEDB;
            ALTER USER blagodarie WITH PASSWORD 'пароль';
            \q
                пароль должен быть в local_settings.py, в
                DATABASE['default']['password']
            createdb -U blagodarie blagodarie_dev

         - web сервер apache2:
            sudo apt install apache2  apache2-utils

         - redis-server:
             (Обязательно!)
                *   для кэша ключей token:url   (для этого обязателен redis)
                *   для кэшировния запросов к апи

         -git
            sudo apt install git

    * Должен быть запущен postgresql сервер

    * mkdir -p ~/venv; cd ~/venv
    * virtualenv -p `which python3` project
    *   sudo mkdir -p /home/www-data/django/
        cd /home/www-data/django/
        sudo mkdir -p MEDIA/project
        sudo chown USERNAME_LINUX:USERNAME_LINUX .
    * git clone https://USERNAME@github.com/USERNAME_GIT/project.git
    * cd /home/www-data/django/project
    * source ~/venv/project/bin/activate
    * pip install -r pip-app.txt
    * deactivate
    * cd /home/www-data/django/project/app/app
    * cp local_settings.py.example local_settings.py
    * внести правки в local_settings.py, в особенности:
        ! SECRET_KEY = '50-значный случайный набор ascii- символов'
        - MEDIA_ROOT = '/home/www-data/django/MEDIA/project'
        - возможно, надо поправить и другие настройки
    * cd /home/www-data/django/project
      ln -s /home/LINUX-USER-NAME/venv/project ENV
            : virtual env, запускаемое из ./manage.py

    *   Инициализация базы данных и статических файлов для Apache
        createdb -U postgres project
        ./manage.py migrate
        ./manage.py createsuperuser
        ./manage.py collectstatic
    
    !!! Проверим работу сервера разработчика:
        cd /home/www-data/django/project/app
        ./manage.py runserver 0.0.0.0:8000
            http://site.name:8000 : что-то должно быть
        Ctrl-C
    
    * Загрузка данных для вычисления фаз луны
        cd /home/www-data/django/project/app
        ./manage.py shell
        load.timescale(builtin=False)
        load('de421.bsp')
        exit()

    * chown -R www-data:www-data ~/venv/project
      chmod 0600 /home/www-data/django/project/app/local_settings.py
      chown -R www-data:www-data /home/www-data/django/project
      chown -R www-data:www-data /home/www-data/django/MEDIA/project

Настройка сервера Apache:

    * Должны быть установлены mod_wsgi и mod_xsendfile.
        sudo apt install libapache2-mod-wsgi-py3 libapache2-mod-xsendfile

    * sudo a2enmod ssl rewrite wsgi headers

    * пример настройки виртуального хоста Apache

    <VirtualHost *:80>
        ServerName project.org

        # Здесь, в папку /.well-known/acme-challenge/,
        # кладем контрольные файлы при формировании
        # сертификатов от https://www.sslforfree.com/.
        # При любом другом запросе, нежели
        # в /.well-known/acme-challenge/,
        # идем на htps://
        #
        DocumentRoot /home/www-data/ssl-for-free
        <Directory /home/www-data/ssl-for-free>
            Require all granted
        </Directory>

        RewriteEngine On
        RewriteCond %{REQUEST_URI} !^/\.well-known/acme-challenge/
        RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI}
    </VirtualHost>

    <VirtualHost *:443>

        ServerName project.org

        SSLEngine on
        SSLProtocol all -SSLv2
        SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM

        SSLCertificateFile /home/www-data/ssl-certificates/sslforfree/project.org/certificate.crt
        SSLCertificateKeyFile /home/www-data/ssl-certificates/sslforfree/project.org/private.key
        SSLCertificateChainFile /home/www-data/ssl-certificates/sslforfree/project.org/ca_bundle.crt

        Alias /media/           /home/www-data/django/MEDIA/project/
        <Directory /home/www-data/django/MEDIA/project/>
            Header set Access-Control-Allow-Origin *
            Header set Access-Control-Allow-Credentials true
            Require all granted
        </Directory>

        <IfModule mod_deflate.c>
            AddOutputFilterByType DEFLATE application/json
        </IfModule>

        Alias /static/          /home/www-data/django/project/app/static/
        <Directory /home/www-data/django/project/app/static/>
            Require all granted
        </Directory>
        Alias /robots.txt       /home/www-data/django/project/app/static/system/robots.txt

        # После maximum-request wsgi- application reloads, во избежание потребления
        # слишком много памяти. Reloads только когда wsgi- application не активно
        # и этого момента ждет graceful-timeout секунд. Если wsgi- application зависло
        # в течение deadlock-timeout, перезагружать его
        #
        WSGIDaemonProcess project.org display-name=%{GROUP} threads=16 maximum-requests=10000 graceful-timeout=7200 deadlock-timeout=60 home=/home/www-data/django/project/app

        WSGIProcessGroup  project.org
        WSGIScriptAlias / /home/www-data/django/project/app/app/wsgi.py

        # Во избежание ошибок: premature end of script headers wsgi.py
        #
        WSGIApplicationGroup %{GLOBAL}

        WSGIPassAuthorization On

        <FilesMatch "wsgi\.py$">
            Require all granted
        </FilesMatch>

    </VirtualHost>]

    * Добавить в конфигурацию (/etc/apache2/conf-enabled) .conf-файл, например,
      с именем reqtimeout.conf следующего содержания:

        # Minimize IOError request data read exeptions when posting data
        #
        # http://stackoverflow.com/questions/3823280/ioerror-request-data-read-error
        # http://httpd.apache.org/docs/2.2/mod/mod_reqtimeout.html
        #
        RequestReadTimeout header=90,MinRate=500 body=90,MinRate=500

        - выполнить sudo a2enmod reqtimeout

    * Очистка "мусора"
      В /etc/crontab такого типа строки:
          15 2 * * * www-data   cd /home/www-data/django/project/app && ./manage.py clearsessions

    * Процедура обновления api:
        см. contrib/update_backend_prod.sh

Установка Telegram Bot
----------------------

    * Д.б. установлено на Linux:
         - redis-server

    (Здесь каталог telegram-bot)

    mkdir -p ~/venv; cd ~/venv
    virtualenv -p `which python3` telegram-bot
    cd telegram-bot
    source ./bin/activate
    pip install -r /путь/к/pip-telegram-bot.txt
    deactivate
    sudo chown -R www-data:www-data .

    #   В git каталоге:
    cd telegram-bot
    sudo ln -s /home/LINUX-USER-NAME/venv/telegram-bot ENV
    sudo chown -R www-data:www-data .
    # В settings_local.py подправить параметры
    sudo chmod 0600 settings_local.py

    # Запуск telegram-bot-server через systemd
    # ----------------------------------------
    #
    cd /etc/systemd/system
    # Создать там файл с именем telegram-bot-prod.service 
    [Unit]
    Description=Start telegram-bot server for blagodarie.org
    After=network.target
    Before=apache2.service

    [Service]
    Type=simple
    Restart=always
    User=www-data
    WorkingDirectory=/home/www-data/django/api_blagodarie_org/telegram-bot
    ExecStart=/home/www-data/django/api_blagodarie_org/telegram-bot/ENV/bin/python3 /home/www-data/django/api_blagodarie_org/telegram-bot/bot_run.py
    
    # /home/www-data/django/api_blagodarie_org/telegram-bot/ENV/bin/python3 :
    #   путь и python в виртуальном окружении
    #
    # /home/www-data/django/api_blagodarie_org/telegram-bot/bot_run.py :
    #   исполняемый файл сервиса

    [Install]
    WantedBy=multi-user.target
    
    # Настройка apache2 на работу c telegram-bot
    # ------------------------------------------
    #
    # Файл конфигурации виртуального хоста apache2
    #
    <VirtualHost *:443>
        ServerName bot.blagodarie.org

        SSLEngine on
        SSLProtocol all -SSLv2
        SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM

        SSLCertificateFile /home/www-data/ssl-certificates/sslforfree/wildcard.blagodarie.org/certificate.crt
        SSLCertificateKeyFile /home/www-data/ssl-certificates/sslforfree/wildcard.blagodarie.org/private.key
        SSLCertificateChainFile /home/www-data/ssl-certificates/sslforfree/wildcard.blagodarie.org/ca_bundle.crt

        SSLEngine On
        SSLProxyEngine On
        # Здесь порт 3001 должен быть согласован с settings_local.py
        ProxyPass / http://127.0.0.1:3001/
        ProxyPassReverse / http://127.0.0.1:3001/

    </VirtualHost>

    # telegram-bot: настройка авторизации на Youtube
    # ----------------------------------------------

    (
        -   Пропустите, если не используете передачу видео из топика группы в Youtube.
        -   Видео инструкция: https://www.youtube.com/watch?v=t0RKgHskYwI, по ней в точности,
            за исключением scope, здесь: https://www.googleapis.com/auth/youtube.upload 
    )

    -   Каталог для временных файлов. Должен существовать.
        Cм. settings.DIR_TEMP, создайте такой каталог или
        укажите в settings_local.py и создайте что указали.
    -   Пользователь Google:
            *   у него в https://console.cloud.google.com/apis/credentials должен быть проект
            *   к проекту (https://console.cloud.google.com/apis/library) подключена
                библиотека YouTube Data API v3
            *   https://console.cloud.google.com/apis/credentials/consent
                !   ВАЖНО. Иначе refresh_token перестанет быть действительным через неделю:
                    publishing status: in production
            *   https://console.cloud.google.com/apis/credentials:
                -   Create Credentials... Oauth client ID... Web Application
                -   Authorized redirect URIs: (полагаю, что работает) http://localhost
                -   Download Oauth client... Download JSON...
                    Сохранить в telegram-bot/client_secrets.json

    -   В адресной строке браузера (в одной строке, здесь несколько для наглядности),
        в браузере вы зарегистрированы пользователем Google:
            https://accounts.google.com/o/oauth2/auth?
                client_id=<client_id>&
                redirect_uri=http://localhost&
                response_type=code&
                scope=https://www.googleapis.com/auth/youtube.upload&
                access_type=offline
            Будут вопросы:
                -   каким пользователем Google регистрируетесь?
                -   небезопасно, эксперты Google не проверяли
                    приложение, тогда Дополнительно..., соглашайтесь
                -   на остальное соглашайтесь
            Должны получить в адресной строке браузера:
                http://localhost/?code=<code>&scope=https://www.googleapis.com/auth/youtube.upload

    -   Например, из консоли Linux (опять таки, в одной строке, но пробел перед и после "..."):
            curl --request POST --data
                "code=<code>&
                 client_id=<client_id>&
                 client_secret=<client_secret>&
                 redirect_uri=http://localhost&
                 grant_type=authorization_code"
                https://oauth2.googleapis.com/token
            Результат:
                {
                    "access_token": "<текуший_access_token>",
                    "expires_in": 3599,
                    "refresh_token": "<вечный_refresh_token>",
                    "scope": "https://www.googleapis.com/auth/youtube.upload",
                    "token_type": "Bearer"
                }
            Будет письмо от Google пользователю с темой
            "Оповещение системы безопасности для аккаунта <user>@gmail.com"
            Игнорируйте. В дальнейшем таких писем не будет.

    !   Для YouTube video upload получено всё необходимое:
            *   client_id
            *   client_secret
            *   refresh_token
        Это надо занести в данные ключа (ид группы) словаря
        GROUPS_WITH_YOUTUBE_UPLOAD в telegram-bot/settings_local.py

    !   Справочно, это реализовано в коде telegram- боте перед загрузкой очередного
        видео.
        Получение нового access_token взамен прежнего, время жизни которого 1 час.
        Например, с помощью curl:
            curl --request POST --data
                "client_id=<client_id>&
                 client_secret=<client_secret>&
                 refresh_token=<вечный_refresh_token>&
                 grant_type=refresh_token"
                https://oauth2.googleapis.com/token
        Результат:
            {
                "access_token": "<текущий_access_token>",
                "expires_in": 3599,
                "scope": "https://www.googleapis.com/auth/youtube.upload",
                "token_type": "Bearer"
            }
