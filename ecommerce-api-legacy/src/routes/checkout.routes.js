'use strict';

const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const createCheckoutController = require('../controllers/checkout.controller');

module.exports = ({ db }) => {
    const router = Router();
    const controller = createCheckoutController({ db });

    router.post('/checkout', asyncHandler(controller.checkout));

    return router;
};
