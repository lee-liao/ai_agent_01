const selfsigned = require('selfsigned');
const fs = require('fs');
const path = require('path');

// Generate SSL certificates for frontend development
const attrs = [{ name: 'commonName', value: 'localhost' }];
const options = {
  keySize: 2048,
  days: 365,
  algorithm: 'sha256',
  extensions: [{
    name: 'basicConstraints',
    cA: true
  }, {
    name: 'subjectAltName',
    altNames: [
      {
        type: 2, // DNS
        value: 'localhost'
      },
      {
        type: 7, // IP
        ip: '127.0.0.1'
      },
      {
        type: 7, // IP
        ip: '192.168.10.210'
      },
      {
        type: 7, // IP
        ip: '192.168.10.244'
      }
    ]
  }]
};

console.log('Generating SSL certificates for frontend...');
const pems = selfsigned.generate(attrs, options);

// Write certificates to files
const certDir = path.join(__dirname, 'sslCertificates');
if (!fs.existsSync(certDir)) {
  fs.mkdirSync(certDir, { recursive: true });
}

fs.writeFileSync(path.join(certDir, 'cert.pem'), pems.cert);
fs.writeFileSync(path.join(certDir, 'key.pem'), pems.private);

console.log('SSL certificates generated:');
console.log('- cert.pem');
console.log('- key.pem');
console.log('Certificates are valid for localhost and IPs: 127.0.0.1, 192.168.10.210, 192.168.10.244');