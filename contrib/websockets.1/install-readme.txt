Установка Websockets server на сервер Apache в Ubuntu Linux.
----------------------------------------------------------------

    (Здесь каталог websockets-server)

    mkdir -p ~/venv; cd ~/venv
    virtualenv -p `which python3` websocket-server
    cd websocket-server
    source ./bin/activate
    pip install -r /путь/к/pip-websockets-server.txt
    deactivate
    sudo chown -R www-data:www-data .

    #   В git каталоге:
    cd websockets-server
    sudo ln -s /home/LINUX-USER-NAME/venv/websocket-server ENV
    sudo chown -R www-data:www-data .
    # В local_settings.py, возможно, надо подправить SERVER_PORT,
    # полагаем его 6789

    # Запуск websocket-server через systemd
    # -------------------------------------
    #
    cd /etc/systemd/system
    # Создать там файл с именем websocket-prod.service 
    [Unit]
    Description=Start websocket server for blagodarie.org
    After=network.target
    Before=apache2.service

    [Service]
    Type=simple
    Restart=always
    User=www-data
    ExecStart=/home/www-data/django/api_blagodarie_org/websockets-server/ENV/bin/python3 /home/www-data/django/api_blagodarie_org/websockets-server/websockets-server.py
    
    # /home/www-data/django/api_blagodarie_org/websockets-server/ENV/bin/python3 :
    #   путь и python в виртуальном окружении
    #
    # /home/www-data/django/api_blagodarie_org/websockets-server/websockets-server.py :
    #   исполняемый файл сервиса

    [Install]
    WantedBy=multi-user.target

    
    
    # Настройка apache2 на работу c websocket-server
    # ----------------------------------------------
    #
    # Файл конфигурации виртуального хоста apache2
    #
    <VirtualHost *:443>
        ServerName wss.blagodarie.org

        SSLEngine on
        SSLProtocol all -SSLv2
        SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM

        SSLCertificateFile /home/www-data/ssl-certificates/sslforfree/wildcard.blagodarie.org/certificate.crt
        SSLCertificateKeyFile /home/www-data/ssl-certificates/sslforfree/wildcard.blagodarie.org/private.key
        SSLCertificateChainFile /home/www-data/ssl-certificates/sslforfree/wildcard.blagodarie.org/ca_bundle.crt

        ProxyPass "/" "ws://127.0.0.1:6789/"
        ProxyPassReverse "/" "ws://127.0.0.1:6789/"

    </VirtualHost>

