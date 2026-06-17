server {
    server_name api.doverabot.ru;

    location /static/ {
        alias /srv/blagodarie/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /srv/blagodarie/app/media/;
    }

    location /robots.txt {
        alias /srv/blagodarie/app/static/system/robots.txt;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
        client_max_body_size 50M;
    }

    listen 443 ssl; # managed by Certbot
    listen [::]:443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/doverabot.ru/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/doverabot.ru/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot


}
server {
    if ($host = api.doverabot.ru) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    listen [::]:80;
    server_name api.doverabot.ru;
    return 404; # managed by Certbot


}
