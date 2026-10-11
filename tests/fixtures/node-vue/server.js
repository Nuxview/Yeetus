const http = require("http");

http.createServer((request, response) => {
  response.end("Hello Vue fixture");
}).listen(8080, "0.0.0.0");
