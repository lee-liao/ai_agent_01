const { createServer } = require('https');
const { parse } = require('url');
const next = require('next');
const fs = require('fs');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const httpsOptions = {
  key: fs.readFileSync(path.join(__dirname, 'sslCertificates/key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'sslCertificates/cert.pem')),
};

app.prepare().then(() => {
  createServer(httpsOptions, (req, res) => {
    const parsedUrl = parse(req.url, true);
    handle(req, res, parsedUrl);
  }).listen(8501, (err) => {
    if (err) throw err;
    console.log('> Ready on https://localhost:8501');
    console.log('> LAN access: https://192.168.10.210:8501');
    console.log('> WAN access: https://103.98.213.149:8501');
  });
});