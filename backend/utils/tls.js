const fs = require("fs");
const https = require("https");
const config = require("../../../backend/config/env");

function readCertificate(path) {
  if (!path) {
    return null;
  }

  if (!fs.existsSync(path)) {
    console.warn(
      `Certificado no encontrado: ${path}`
    );

    return null;
  }

  return fs.readFileSync(path);
}

function createHttpsAgent() {
  const certificates = [
    readCertificate(
      config.datacredito.certificates.root
    ),

    readCertificate(
      config.datacredito.certificates.ev
    ),

    readCertificate(
      config.datacredito.certificates.ov
    )
  ].filter(Boolean);

  return new https.Agent({
    ca:
      certificates.length > 0
        ? certificates
        : undefined,

    rejectUnauthorized: true,

    keepAlive: true
  });
}

module.exports = {
  createHttpsAgent
};