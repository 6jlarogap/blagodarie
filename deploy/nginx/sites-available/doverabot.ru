gzip_vary on;
gzip_proxied any;
gzip_types application/json application/javascript text/css;

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name doverabot.ru map.doverabot.ru;

    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    root /srv/blagodarie/frontend/map_npm/dist;
    index index.html;

    location /assets/ {
        try_files $uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location /common/ {
        alias /srv/blagodarie/frontend/common/;
    }

    location = /rent {
        return 301 /rent/;
    }

    location /rent/ {
        alias /srv/blagodarie/frontend/rent_map/;
        index index.html;
    }

    location = /auth/telegram {
        proxy_pass http://127.0.0.1:8000/api/auth/telegram/;
        proxy_set_header Host api.doverabot.ru;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
        client_max_body_size 50M;
    }

    location = /auth/telegram/ {
        proxy_pass http://127.0.0.1:8000/api/auth/telegram/;
        proxy_set_header Host api.doverabot.ru;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
        client_max_body_size 50M;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name www.doverabot.ru;

    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 301 https://doverabot.ru$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name d2.doverabot.ru;

    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    root /srv/blagodarie/frontend/genesis;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name d3.doverabot.ru;

    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    root /srv/blagodarie/frontend/graph_npm/dist;
    index index.html;

    location /assets/ {
        try_files $uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name mgraph.doverabot.ru;

    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    root /srv/blagodarie/frontend/mgraph/dist;
    index index.html;

    location /assets/ {
        try_files $uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name health.doverabot.ru;

    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 503;
}

server {
    listen 80;
    listen [::]:80;
    server_name doverabot.ru www.doverabot.ru map.doverabot.ru d2.doverabot.ru d3.doverabot.ru mgraph.doverabot.ru health.doverabot.ru;

    return 301 https://$host$request_uri;
}
