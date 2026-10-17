'use strict';

const { validateUserId } = require('../validators/user.validator');
const userService = require('../services/user.service');

module.exports = ({ db }) => ({
    async remove(req, res) {
        const userId = validateUserId(req.params.id);
        await userService.removeUser(db, userId);
        res.status(200).send('Usuário deletado');
    },
});
