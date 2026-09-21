const axios = require("axios");

const config = require("../config/env");
const {
  createHttpsAgent
} = require("../utils/tls");

const logger = require("../utils/logger");

class DatacreditoAuthService {
  constructor(environment) {
    this.environment = environment;

    this.config =
      environment === "preselecta"
        ? config.datacredito.preselecta
        : config.datacredito.income;

    this.httpsAgent =
      createHttpsAgent();

    this.cachedToken = null;

    this.tokenExpiration = 0;
  }

  async getAccessToken() {
    const now = Date.now();

    if (
      this.cachedToken &&
      now < this.tokenExpiration
    ) {
      return this.cachedToken;
    }

    return this.requestNewToken();
  }

  async requestNewToken() {
    const credentials = Buffer.from(
      `${this.config.clientId}:${this.config.clientSecret}`
    ).toString("base64");

    const body = new URLSearchParams();

    body.append(
      "grant_type",
      "password"
    );

    body.append(
      "username",
      this.config.username
    );

    body.append(
      "password",
      this.config.password
    );

    body.append(
      "scope",
      this.config.scope
    );

    try {
      logger.info(
        "Solicitando nuevo access_token",
        {
          environment:
            this.environment,
          tokenUrl:
            this.config.tokenUrl,
          scope:
            this.config.scope
        }
      );

      const response =
        await axios.post(
          this.config.tokenUrl,
          body.toString(),
          {
            timeout:
              config.datacredito.timeout,

            httpsAgent:
              this.httpsAgent,

            headers: {
              Authorization:
                `Basic ${credentials}`,

              "Content-Type":
                "application/x-www-form-urlencoded",

              Accept:
                "application/json"
            }
          }
        );

      if (
        !response.data ||
        !response.data.access_token
      ) {
        throw new Error(
          "Datacrédito no retornó access_token"
        );
      }

      this.cachedToken =
        response.data.access_token;

      const expiresIn =
        Number(
          response.data.expires_in ||
          3600
        );

      // Renovar 60 segundos antes
      // de la expiración.
      this.tokenExpiration =
        Date.now() +
        Math.max(
          60,
          expiresIn - 60
        ) *
          1000;

      logger.info(
        "Access token obtenido correctamente",
        {
          environment:
            this.environment,
          expiresIn
        }
      );

      return this.cachedToken;
    } catch (err) {
      logger.error(
        "Error obteniendo access_token",
        {
          environment:
            this.environment,

          status:
            err.response?.status,

          response:
            err.response?.data,

          message:
            err.message
        }
      );

      throw new Error(
        "No fue posible autenticar contra Datacrédito"
      );
    }
  }

  clearToken() {
    this.cachedToken = null;
    this.tokenExpiration = 0;
  }
}

module.exports =
  DatacreditoAuthService;