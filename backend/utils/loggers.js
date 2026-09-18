function sanitize(value) {
  if (!value) {
    return value;
  }

  if (typeof value === "string") {
    return value
      .replace(
        /Bearer\s+[A-Za-z0-9._-]+/gi,
        "Bearer [REDACTED]"
      )
      .replace(
        /Basic\s+[A-Za-z0-9+/=]+/gi,
        "Basic [REDACTED]"
      );
  }

  if (typeof value === "object") {
    const clone = JSON.parse(
      JSON.stringify(value)
    );

    const sensitiveFields = [
      "password",
      "client_secret",
      "access_token",
      "token",
      "authorization",
      "Authorization"
    ];

    function recursive(obj) {
      if (!obj || typeof obj !== "object") {
        return;
      }

      for (const key of Object.keys(obj)) {
        if (
          sensitiveFields.includes(key)
        ) {
          obj[key] = "[REDACTED]";
        } else if (
          typeof obj[key] === "object"
        ) {
          recursive(obj[key]);
        }
      }
    }

    recursive(clone);

    return clone;
  }

  return value;
}

function info(message, data) {
  console.log(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      level: "INFO",
      message,
      data: sanitize(data)
    })
  );
}

function error(message, data) {
  console.error(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      level: "ERROR",
      message,
      data: sanitize(data)
    })
  );
}

module.exports = {
  info,
  error,
  sanitize
};