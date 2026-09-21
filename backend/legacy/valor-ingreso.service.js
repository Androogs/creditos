const axios = require("axios");

const config = require("../config/env");

const {
  createHttpsAgent
} = require("../utils/tls");

const {
  DatacreditoAuthService
} = require("./datacredito-auth.service");

const logger = require("../utils/logger");

class ValorIngresoService {
  constructor() {
    this.auth =
      new DatacreditoAuthService(
        "income"
      );

    this.httpsAgent =
      createHttpsAgent();
  }

  async consultar(params) {
    const token =
      await this.auth.getAccessToken();

    const headers = {
      access_token: token,

      client_id:
        config.datacredito
          .income
          .clientId,

      client_secret:
        config.datacredito
          .income
          .clientSecret,

      Accept:
        "application/json",

      "Accept-Encoding":
        "gzip,deflate"
    };

    try {
      const response =
        await axios.get(
          config.datacredito
            .income
            .serviceUrl,

          {
            params,

            timeout:
              config.datacredito
                .timeout,

            httpsAgent:
              this.httpsAgent,

            headers
          }
        );

      logger.info(
        "Consulta Valor Ingreso ejecutada",
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

        const newToken =
          await this.auth.getAccessToken();

        const retryResponse =
          await axios.get(
            config.datacredito
              .income
              .serviceUrl,

            {
              params,

              timeout:
                config.datacredito
                  .timeout,

              httpsAgent:
                this.httpsAgent,

              headers: {
                ...headers,
                access_token:
                  newToken
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
        "Error consumiendo Valor Ingreso",
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
  ValorIngresoService;