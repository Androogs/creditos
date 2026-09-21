const express =
  require("express");

const router =
  express.Router();

const controller =
  require("../controllers/datacredito.controller");

const {
  validatePreselecta,
  validateValorIngreso
} =
  require("../middleware/validation.middleware");

router.post(
  "/preselecta/decision",
  validatePreselecta,
  controller.preselecta
);

router.post(
  "/valor-ingreso",
  validateValorIngreso,
  controller.valorIngreso
);

module.exports =
  router;