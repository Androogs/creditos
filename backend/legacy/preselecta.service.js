const axios = require("axios");

const config = require("../config/env");
const {
  createHttpsAgent
} = require("../utils/tls");

const {
  DatacreditoAuthService
} = require("./datacredito-auth.service");

const logger = require("../utils/logger");

class PreselectaService {
  constructor() {
    this.auth =
      new DatacreditoAuthService(
        "preselecta"
      );

    this.httpsAgent =
      createHttpsAgent();
  }

  async decision(payload) {
    const token =
      await this.auth.getAccessToken();

    try {
      const response =
        await axios.post(
          config.datacredito
            .preselecta
            .serviceUrl,

          payload,

          {
            timeout:
              config.datacredito.timeout,

            httpsAgent:
              this.httpsAgent,

            headers: {
              access_token:
                token,

              client_id:
                config.datacredito
                  .preselecta
                  .clientId,

              client_secret:
                config.datacredito
                  .preselecta
                  .clientSecret,

              "Content-Type":
                "application/json",

              Accept:
                "application/json"
            }
          }
        );

      logger.info(
        "Consulta Preselecta ejecutada",
        {
          status:
            response.status
        }
      );

      return {
        success: true,
        status: response.status,
        data: response.data
      };
    } catch (err) {
      if (
        err.response?.status === 401 ||
        err.response?.status === 403
      ) {
        this.auth.clearToken();

        logger.info(
          "Token rechazado. Reintentando autenticación."
        );

        const newToken =
          await this.auth.getAccessToken();

        const retryResponse =
          await axios.post(
            config.datacredito
              .preselecta
              .serviceUrl,

            payload,

            {
              timeout:
                config.datacredito
                  .timeout,

              httpsAgent:
                this.httpsAgent,

              headers: {
                access_token:
                  newToken,

                client_id:
                  config.datacredito
                    .preselecta
                    .clientId,

                client_secret:
                  config.datacredito
                    .preselecta
                    .clientSecret,

                "Content-Type":
                  "application/json",

                Accept:
                  "application/json"
              }
            }
          );

        return {
          success: true,
          status:
            retryResponse.status,
          data:
            retryResponse.data
        };
      }

      logger.error(
        "Error consumiendo Preselecta",
        {
          status:
            err.response?.status,

          response:
            err.response?.data,

          message:
            err.message
        }
      );

      throw err;
    }
  }
}

module.exports =
  PreselectaService;