#
# Template parameters:
# domain: domain name for this vhost
# user: domain owner
#
server {
    listen 443;

    server_name {domain};

    ssl on;

    ssl_certificate		{sslcrt};
    ssl_certificate_key	{sslkey};

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;

    ssl_stapling on;
    ssl_stapling_verify on;

    set $user "{user}";
    set $domain "{domain}";

    set $root  /home/$user/domains/$domain/public_html;
    set $domainlog  $domain;

    if ($user = "") {
        set $root /var/www/html;
        set $domainlog  ip;
    }

    set $deflate $root/.htdeflate;

    gzip_disable msie6;
    gzip_vary on;
    gzip_proxied off;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        log_not_found on;
        root        $root;

        if ( -f $deflate ) {
            gzip on;
        }

        proxy_redirect    off;

        proxy_set_header  Cookie    $http_cookie;
        proxy_set_header  Host      $host;
        proxy_set_header  X-Real-IP $remote_addr;
        proxy_set_header  X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass        https://backendssl;
    }

    location ~ /\.ht {
        deny  all;
    }

    location ~* ^/(phpmyadmin|webmail|squirrelmail|uebimiau|roundcube)/.+\.(jpg|jpeg|gif|png|ico|css|zip|tar|tgz|gz|rar|bz2|doc|xls|exe|pdf|ppt|txt|tar|wav|bmp|rtf|js|wmv|avi|cur|swf|mp3|wma|htc|cur)$ {
        expires     24h;
        root        /var/www/html;
    }

    location @back {
        if ( -f $deflate ) {
            gzip on;
        }

        proxy_pass         https://backendssl;
        proxy_redirect     off;
        proxy_set_header   Host             $host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
    }

    location ~* ^.+\.(css|js|txt|xml)$ {
        expires max;

        root $root;
        if ( -f $deflate ) {
            gzip on;
        }

        error_page      404 405 =       @back;
    }

    location ~* ^.+\.(jpg|jpeg|gif|png|ico|zip|tar|tgz|gz|rar|bz2|doc|xls|exe|pdf|ppt|txt|tar|wav|bmp|rtf|wmv|avi|cur|swf|mp3|wma|htc|cur|3gp|mp4|jar|sis)$ {
        tcp_nodelay off;

        expires     max;
        root        $root;

        error_page	404 405	=	@back;
    }
}
