const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { createCheckoutController } = require('../controllers/checkout.controller');

function buildCheckoutRoutes({ db }) {
  const router = express.Router();
  const controller = createCheckoutController({ db });

  router.post('/checkout', asyncHandler(controller.checkout));
  return router;
}

module.exports = { buildCheckoutRoutes };
