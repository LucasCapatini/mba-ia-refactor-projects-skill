'use strict';

const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const createUserController = require('../controllers/user.controller');

module.exports = ({ db }) => {
    const router = Router();
    const controller = createUserController({ db });

    router.delete('/users/:id', asyncHandler(controller.remove));

    return router;
};
