// HTTP ↔ caso de uso de checkout.
const { validateCheckout } = require('../validators/checkout.validator');
const checkoutService = require('../services/checkout.service');

function createCheckoutController({ db }) {
  return {
    async checkout(req, res) {
      const input = validateCheckout(req.body);
      const { enrollmentId } = await checkoutService.checkout(db, input);
      res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
  };
}

module.exports = { createCheckoutController };
