const http = require("http");

http.createServer((request, response) => {
  response.end("Hello React fixture");
}).listen(3000, "0.0.0.0");
