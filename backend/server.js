const express =
  require("express");

const cors =
  require("cors");

const helmet =
  require("helmet");

const morgan =
  require("morgan");

const config =
  require("./config/env");

const datacreditoRoutes =
  require("./routes/datacredito.routes");

const errorMiddleware =
  require("./middleware/error.middleware");

const logger =
  require("./utils/logger");

const app =
  express();

app.use(
  helmet()
);

app.use(
  cors({
    origin:
      config.frontendUrl
  })
);

app.use(
  express.json({
    limit: "1mb"
  })
);

app.use(
  express.urlencoded({
    extended: true
  })
);

app.use(
  morgan("combined")
);

app.get(
  "/health",
  (req, res) => {
    res.json({
      success: true,
      service:
        "backend-integracion-datacredito",
      environment:
        config.nodeEnv,
      timestamp:
        new Date().toISOString()
    });
  }
);

app.use(
  "/api/datacredito",
  datacreditoRoutes
);

app.use(
  (req, res) => {
    res.status(404).json({
      success: false,
      message:
        "Ruta no encontrada"
    });
  }
);

app.use(
  errorMiddleware
);

app.listen(
  config.port,
  () => {
    logger.info(
      "Servidor iniciado",
      {
        port:
          config.port,

        environment:
          config.nodeEnv
      }
    );
  }
);