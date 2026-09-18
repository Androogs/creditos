require("dotenv").config();

function required(name) {
  const value = process.env[name];

  if (!value) {
    throw new Error(
      `Falta la variable de entorno obligatoria: ${name}`
    );
  }

  return value;
}

module.exports = {
  port: Number(process.env.PORT || 3000),

  nodeEnv: process.env.NODE_ENV || "development",

  frontendUrl:
    process.env.FRONTEND_URL || "http://localhost:5173",

  datacredito: {
    timeout: Number(
      process.env.DATACREDITO_TIMEOUT || 30000
    ),

    preselecta: {
      tokenUrl: required(
        "DATACREDITO_PRESELECTA_TOKEN_URL"
      ),

      serviceUrl: required(
        "DATACREDITO_PRESELECTA_SERVICE_URL"
      ),

      clientId: required(
        "DATACREDITO_PRESELECTA_CLIENT_ID"
      ),

      clientSecret: required(
        "DATACREDITO_PRESELECTA_CLIENT_SECRET"
      ),

      username: required(
        "DATACREDITO_PRESELECTA_USERNAME"
      ),

      password: required(
        "DATACREDITO_PRESELECTA_PASSWORD"
      ),

      scope:
        process.env.DATACREDITO_PRESELECTA_SCOPE ||
        "expco_preselecta"
    },

    income: {
      tokenUrl: required(
        "DATACREDITO_INCOME_TOKEN_URL"
      ),

      serviceUrl: required(
        "DATACREDITO_INCOME_SERVICE_URL"
      ),

      clientId: required(
        "DATACREDITO_INCOME_CLIENT_ID"
      ),

      clientSecret: required(
        "DATACREDITO_INCOME_CLIENT_SECRET"
      ),

      username: required(
        "DATACREDITO_INCOME_USERNAME"
      ),

      password: required(
        "DATACREDITO_INCOME_PASSWORD"
      ),

      scope:
        process.env.DATACREDITO_INCOME_SCOPE ||
        "expco_incomes"
    },

    certificates: {
      root:
        process.env.DATACREDITO_CA_ROOT,

      ev:
        process.env.DATACREDITO_CA_EV,

      ov:
        process.env.DATACREDITO_CA_OV
    }
  }
};