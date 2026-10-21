const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { createUserController } = require('../controllers/user.controller');

function buildUserRoutes({ db }) {
  const router = express.Router();
  const controller = createUserController({ db });

  router.delete('/users/:id', asyncHandler(controller.remove));
  return router;
}

module.exports = { buildUserRoutes };
