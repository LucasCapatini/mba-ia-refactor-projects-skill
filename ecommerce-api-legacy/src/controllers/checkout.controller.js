'use strict';

const { validateCheckout } = require('../validators/checkout.validator');
const checkoutService = require('../services/checkout.service');

module.exports = ({ db }) => ({
    async checkout(req, res) {
        const input = validateCheckout(req.body);
        const { enrollmentId } = await checkoutService.checkout(db, input);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
});
