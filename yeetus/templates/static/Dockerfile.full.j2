FROM nginx:alpine

WORKDIR /usr/share/nginx/html

COPY . .

RUN mkdir -p /var/cache/nginx /run/nginx \
    && chown -R nginx:nginx /var/cache/nginx /run/nginx \
    && sed -i 's@^pid .*;@pid /run/nginx/nginx.pid;@' /etc/nginx/nginx.conf

USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
